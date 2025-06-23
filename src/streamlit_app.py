import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import numpy as np
import plotly.graph_objects as go
import warnings

warnings.filterwarnings('ignore')

# --- Configuración de la Página y Estilos ---
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""<style>
/* Estilos generales */
.stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
.stMetric { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 4px solid #0d6efd; }
.stTabs [data-baseweb="tab-list"] { gap: 5px; }
.stTabs [data-baseweb="tab"] { height: 45px; padding: 0 20px; background-color: #e9ecef; border-radius: 8px !important; font-weight: 500; transition: all 0.3s ease; }
.stTabs [aria-selected="true"] { background-color: #0d6efd !important; color: white !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.stButton>button { border-radius: 8px; font-weight: 500; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #2c3e50, #1a1a2e); color: white; }
[data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stTextInput label { color: white !important; }
h1, h2, h3, h4, h5, h6 { color: #2c3e50; font-weight: 600; }
</style>""", unsafe_allow_html=True)

# ==============================================================================
# FUNCIONES DE AUTENTICACIÓN Y API DE IOL
# ==============================================================================

def obtener_tokens(usuario, contraseña):
    """Autentica al usuario y guarda los tokens en session_state."""
    url_login = 'https://api.invertironline.com/token'
    datos = {'username': usuario, 'password': contraseña, 'grant_type': 'password'}
    try:
        respuesta = requests.post(url_login, data=datos, timeout=15)
        respuesta.raise_for_status()
        data = respuesta.json()
        st.session_state['access_token'] = data['access_token']
        st.session_state['refresh_token'] = data['refresh_token']
        st.session_state['logged_in'] = True
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Error de autenticación: {e.response.status_code}. Verifique sus credenciales.")
        return False
    except Exception as e:
        st.error(f"Error inesperado al obtener tokens: {e}")
        return False

def obtener_encabezado_autorizacion():
    """Crea el encabezado de autorización para las llamadas a la API."""
    return {'Authorization': f'Bearer {st.session_state.get("access_token", "")}'}

@st.cache_data(ttl=600)
def obtener_lista_clientes(_token): # _token es para invalidar la caché cuando cambia
    """Obtiene la lista de clientes de un asesor."""
    url = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    try:
        respuesta = requests.get(url, headers=obtener_encabezado_autorizacion(), timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()
    except Exception as e:
        st.error(f"Error al obtener la lista de clientes: {e}")
        return []

@st.cache_data(ttl=300)
def obtener_portafolio(_token, id_cliente, pais='Argentina'):
    """Obtiene el portafolio de un cliente específico."""
    url = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    try:
        respuesta = requests.get(url, headers=obtener_encabezado_autorizacion(), timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()
    except Exception as e:
        st.error(f"Error al obtener el portafolio: {e}")
        return None

@st.cache_data(ttl=300)
def obtener_serie_historica(_token, simbolo, mercado, fecha_desde, fecha_hasta):
    """Obtiene la serie histórica de precios para un activo."""
    url = f"https://api.invertironline.com/api/v2/{mercado.upper()}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/sinAjustar"
    try:
        respuesta = requests.get(url, headers=obtener_encabezado_autorizacion(), timeout=20)
        if respuesta.status_code in [400, 404]: return None
        respuesta.raise_for_status()
        return respuesta.json()
    except Exception:
        return None

# ==============================================================================
# FUNCIONES DE PROCESAMIENTO Y ANÁLISIS DE DATOS
# ==============================================================================

def obtener_datos_historicos_portafolio(token, id_cliente, fecha_desde, fecha_hasta):
    """Orquesta la obtención de datos históricos para todos los activos del portafolio."""
    portafolio = obtener_portafolio(token, id_cliente)
    if not portafolio or 'activos' not in portafolio:
        st.warning("No se pudo cargar el portafolio o está vacío.")
        return pd.DataFrame(), {}

    activos = [a for a in portafolio['activos'] if a.get('cantidad', 0) > 0 and a.get('titulo', {}).get('simbolo')]
    if not activos:
        st.warning("No hay activos con cantidad positiva en el portafolio.")
        return pd.DataFrame(), {}

    precios_historicos = {}
    pesos_actuales = {}
    mercados_fallback = ['BCBA', 'ROFEX', 'NASDAQ', 'NYSE', 'MAE']
    
    total_activos = len(activos)
    progress_bar = st.progress(0, text=f"Iniciando descarga de datos para {total_activos} activos...")

    for i, activo in enumerate(activos):
        simbolo = activo['titulo']['simbolo']
        mercado_primario = activo['titulo'].get('mercado', 'BCBA')
        progress_text = f"({i+1}/{total_activos}) Buscando datos para {simbolo}..."
        progress_bar.progress((i + 1) / total_activos, text=progress_text)
        
        serie_data = obtener_serie_historica(token, simbolo, mercado_primario, fecha_desde, fecha_hasta)
        
        if not serie_data:
            for mercado_alt in mercados_fallback:
                if mercado_alt.upper() == mercado_primario.upper(): continue
                serie_data = obtener_serie_historica(token, simbolo, mercado_alt, fecha_desde, fecha_hasta)
                if serie_data: break

        if serie_data:
            df = pd.DataFrame(serie_data)
            df['fechaHora'] = pd.to_datetime(df['fechaHora'])
            df = df.set_index('fechaHora')['cierre']
            precios_historicos[simbolo] = df
            pesos_actuales[simbolo] = activo['cantidad']
    
    progress_bar.empty()
    if not precios_historicos:
        st.error("No se pudieron obtener datos históricos para ningún activo del portafolio.")
        return pd.DataFrame(), {}

    df_precios = pd.DataFrame(precios_historicos).ffill().bfill()
    return df_precios, pesos_actuales

def calcular_estadisticas(df_precios, pesos):
    """Calcula las estadísticas clave del portafolio."""
    retornos = df_precios.pct_change().dropna()
    if retornos.empty:
        return None

    retorno_anualizado_activos = retornos.mean() * 252
    
    # Calcular pesos basados en el valor de mercado más reciente
    valor_mercado_reciente = df_precios.iloc[-1] * pd.Series(pesos)
    total_valorizado = valor_mercado_reciente.sum()
    if total_valorizado == 0: return None
    weights = valor_mercado_reciente / total_valorizado
    
    retorno_portafolio = np.sum(retorno_anualizado_activos * weights)
    cov_matrix = retornos.cov() * 252
    volatilidad_portafolio = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    return {
        "retornos_diarios_portafolio": retornos.dot(weights),
        "retorno_anualizado_portafolio": retorno_portafolio,
        "volatilidad_anualizada_portafolio": volatilidad_portafolio,
        "pesos": weights,
        "matriz_correlacion": retornos.corr()
    }

# ==============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ==============================================================================

def mostrar_portafolio_actual(token, id_cliente):
    st.header("Composición del Portafolio Actual")
    portafolio_data = obtener_portafolio(token, id_cliente)
    if portafolio_data and 'activos' in portafolio_data:
        activos_list = []
        for a in portafolio_data['activos']:
            if a.get('cantidad', 0) > 0:
                activos_list.append({
                    'Símbolo': a.get('titulo', {}).get('simbolo'),
                    'Mercado': a.get('titulo', {}).get('mercado'),
                    'Cantidad': a.get('cantidad'),
                    'Valorizado ($)': f"{a.get('valorizado', 0):,.2f}"
                })
        if activos_list:
            df_display = pd.DataFrame(activos_list)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("El portafolio no tiene activos con cantidad mayor a cero.")
    else:
        st.warning("No se pudo cargar la información del portafolio.")

def mostrar_analisis_historico(token, id_cliente):
    st.header("Análisis Histórico del Portafolio")
    
    col1, col2 = st.columns(2)
    fecha_hasta = date.today()
    fecha_desde = col1.date_input("Fecha Desde", fecha_hasta - timedelta(days=365))
    fecha_hasta_input = col2.date_input("Fecha Hasta", fecha_hasta)

    if st.button("🚀 Analizar Portafolio"):
        if fecha_desde >= fecha_hasta_input:
            st.error("La fecha 'Desde' debe ser anterior a la fecha 'Hasta'.")
            return

        with st.spinner("Obteniendo y procesando datos del portafolio... Esto puede tardar unos minutos."):
            df_precios, pesos = obtener_datos_historicos_portafolio(token, id_cliente, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta_input.strftime('%Y-%m-%d'))

            if df_precios.empty:
                st.warning("No se encontraron datos para el análisis.")
                return

            stats = calcular_estadisticas(df_precios, pesos)
            if not stats:
                st.error("No se pudieron calcular las estadísticas. Verifique los datos de los activos.")
                return
            
            st.subheader("Métricas Clave del Portafolio")
            col1, col2 = st.columns(2)
            col1.metric("Retorno Anualizado Estimado", f"{stats['retorno_anualizado_portafolio']:.2%}")
            col2.metric("Volatilidad Anualizada Estimada", f"{stats['volatilidad_anualizada_portafolio']:.2%}")
            
            st.subheader("Rendimiento Acumulado del Portafolio")
            ret_acumulado = (1 + stats['retornos_diarios_portafolio']).cumprod()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ret_acumulado.index, y=ret_acumulado, name='Portafolio', mode='lines'))
            fig.update_layout(title='Evolución del Portafolio', xaxis_title='Fecha', yaxis_title='Rendimiento Acumulado')
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Correlación de Activos")
            corr_matrix = stats['matriz_correlacion']
            fig_corr = go.Figure(data=go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.columns, colorscale='Viridis'))
            st.plotly_chart(fig_corr, use_container_width=True)

# ==============================================================================
# APLICACIÓN PRINCIPAL
# ==============================================================================

def main():
    st.sidebar.title("Panel de Asesor IOL")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.sidebar.header("Inicio de Sesión")
        usuario = st.sidebar.text_input("Usuario", key="user_main")
        contraseña = st.sidebar.text_input("Contraseña", type="password", key="pass_main")
        if st.sidebar.button("Login", key="login_btn_main"):
            if not usuario or not contraseña:
                st.sidebar.warning("Por favor, ingrese usuario y contraseña.")
                return
            with st.spinner('Autenticando...'):
                if obtener_tokens(usuario, contraseña):
                    st.rerun()
                else:
                    st.sidebar.error("Login fallido.")
    else:
        st.sidebar.success(f"Conectado exitosamente.")
        
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        token = st.session_state.get('access_token')
        if not token:
            st.error("Sesión inválida. Por favor, inicie sesión de nuevo.")
            st.session_state['logged_in'] = False
            # No need to rerun here, will be handled on next script run
            return

        clientes = obtener_lista_clientes(token)
        if not clientes:
            st.error("No se pudieron cargar los clientes o no tiene clientes asignados.")
            return

        clientes_dict = {f"{c['nombre']} ({c['numero']})": c['id'] for c in clientes}
        cliente_seleccionado_nombre = st.sidebar.selectbox("Seleccione un Cliente", options=list(clientes_dict.keys()))
        id_cliente_seleccionado = clientes_dict[cliente_seleccionado_nombre]

        st.title(f"Dashboard para: {cliente_seleccionado_nombre}")

        tab1, tab2 = st.tabs(["📊 Portafolio Actual", "📈 Análisis Histórico"])

        with tab1:
            mostrar_portafolio_actual(token, id_cliente_seleccionado)

        with tab2:
            mostrar_analisis_historico(token, id_cliente_seleccionado)

if __name__ == "__main__":
    main()

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
        "🔄 Optimización"
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio)
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor"),
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
