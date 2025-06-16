import streamlit as st
import pandas as pd
import numpy as np
import requests
import warnings
from datetime import date, timedelta, datetime

# Suprimir warnings
warnings.filterwarnings('ignore')

# === CONFIGURACIÓN DE LA APLICACIÓN ===
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILOS CSS ===
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stMetric {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #0d6efd;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0 20px;
        background-color: #e9ecef;
        border-radius: 8px !important;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0d6efd !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50, #1a1a2e);
        color: white;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# === FUNCIONES DE API IOL ===

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
            return respuesta.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener cotización MEP: {str(e)}')
        return None

# === FUNCIONES DE ANÁLISIS ===

def mostrar_resumen_portafolio(portafolio):
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
            
            # Buscar valuación en diferentes campos posibles
            campos_valuacion = [
                'valuacionEnMonedaOriginal', 'valuacionActual', 'valuacion',
                'valorActual', 'montoInvertido', 'valorMercado', 'valorTotal'
            ]
            
            valuacion = 0
            for campo in campos_valuacion:
                if campo in activo and activo[campo] is not None:
                    try:
                        valuacion = float(activo[campo])
                        if valuacion > 0:
                            break
                    except (ValueError, TypeError):
                        continue
            
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
        
        # Información General
        cols = st.columns(4)
        cols[0].metric("Total de Activos", len(datos_activos))
        cols[1].metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        cols[2].metric("Tipos de Activos", df_activos['Tipo'].nunique())
        cols[3].metric("Valor Total", f"${valor_total:,.2f}")
        
        # Tabla de activos
        st.subheader("📋 Detalle de Activos")
        df_display = df_activos.copy()
        df_display['Valuación'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "N/A"
        )
        if valor_total > 0:
            df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
        else:
            df_display['Peso (%)'] = 0
        df_display = df_display.sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, height=400)
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
                        cotizacion_mep = obtener_cotizacion_mep(token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta)
                    
                    if cotizacion_mep:
                        st.success(f"✅ Cotización MEP para {simbolo_mep}")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Compra", f"${cotizacion_mep.get('cotizacionCompra', 0):.2f}")
                        col2.metric("Venta", f"${cotizacion_mep.get('cotizacionVenta', 0):.2f}")
                        col3.metric("Spread", f"${cotizacion_mep.get('spread', 0):.2f}")
                        
                        # Mostrar detalles adicionales si están disponibles
                        if 'fechaHora' in cotizacion_mep:
                            st.info(f"📅 Última actualización: {cotizacion_mep['fechaHora']}")
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.markdown("### 🔄 Optimización de Portafolio")
    
    st.info("""
    **Funcionalidad en Desarrollo**
    
    Esta sección incluirá:
    - 📊 Análisis de correlación entre activos
    - ⚖️ Optimización de pesos por estrategia
    - 📈 Frontera eficiente
    - 🎯 Simulaciones de Monte Carlo
    """)
    
    if st.button("🚀 Ejecutar Análisis Básico"):
        with st.spinner("Analizando portafolio..."):
            portafolio = obtener_portafolio(token_acceso, id_cliente)
            
            if portafolio:
                activos = portafolio.get('activos', [])
                
                if activos:
                    st.success(f"✅ Portafolio encontrado con {len(activos)} activos")
                    
                    # Análisis básico de distribución
                    valores = []
                    tipos = []
                    
                    for activo in activos:
                        try:
                            titulo = activo.get('titulo', {})
                            tipo = titulo.get('tipo', 'N/A')
                            tipos.append(tipo)
                            
                            # Buscar valuación
                            campos_valuacion = ['valuacion', 'valorActual', 'montoInvertido']
                            valuacion = 0
                            
                            for campo in campos_valuacion:
                                if campo in activo and activo[campo]:
                                    try:
                                        valuacion = float(activo[campo])
                                        break
                                    except:
                                        continue
                            
                            valores.append(valuacion)
                        except:
                            continue
                    
                    if valores:
                        # Mostrar estadísticas básicas
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Valor Total", f"${sum(valores):,.2f}")
                        col2.metric("Valor Promedio", f"${np.mean(valores):,.2f}")
                        col3.metric("Desviación Estándar", f"${np.std(valores):,.2f}")
                        
                        # Distribución por tipo
                        df_tipos = pd.DataFrame({'Tipo': tipos, 'Valor': valores})
                        distribución_tipos = df_tipos.groupby('Tipo')['Valor'].sum().reset_index()
                        
                        st.subheader("📊 Distribución por Tipo de Activo")
                        st.dataframe(distribución_tipos, use_container_width=True)
                    else:
                        st.warning("No se pudieron extraer valores de los activos")
                else:
                    st.warning("El portafolio está vacío")
            else:
                st.error("No se pudo obtener el portafolio")

# === APLICACIÓN PRINCIPAL ===

def main():
    """Función principal de la aplicación Streamlit"""
    
    # Inicializar session state
    if 'token_acceso' not in st.session_state:
        st.session_state.token_acceso = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    if 'clientes' not in st.session_state:
        st.session_state.clientes = []
    
    # Título principal
    st.title("📊 IOL Portfolio Analyzer")
    st.markdown("### Análisis de Portafolios - Invertir Online")
    
    # Sidebar para autenticación
    with st.sidebar:
        st.header("🔐 Autenticación")
        
        if st.session_state.token_acceso is None:
            with st.form("login_form"):
                usuario = st.text_input("Usuario:")
                contraseña = st.text_input("Contraseña:", type="password")
                submit_login = st.form_submit_button("🔓 Iniciar Sesión")
                
                if submit_login and usuario and contraseña:
                    with st.spinner("Autenticando..."):
                        token_acceso, refresh_token = obtener_tokens(usuario, contraseña)
                        
                        if token_acceso:
                            st.session_state.token_acceso = token_acceso
                            st.session_state.refresh_token = refresh_token
                            st.success("✅ Autenticación exitosa")
                            st.rerun()
                        else:
                            st.error("❌ Error en la autenticación")
        else:
            st.success("✅ Sesión activa")
            
            # Obtener lista de clientes
            if not st.session_state.clientes:
                with st.spinner("Obteniendo clientes..."):
                    clientes = obtener_lista_clientes(st.session_state.token_acceso)
                    st.session_state.clientes = clientes
            
            # Selector de cliente
            if st.session_state.clientes:
                opciones_clientes = ["Cuenta propia"] + [
                    f"{cliente.get('nombre', 'N/A')} ({cliente.get('id', 'N/A')})"
                    for cliente in st.session_state.clientes
                ]
                
                cliente_seleccionado = st.selectbox(
                    "👤 Seleccionar Cliente:",
                    opciones_clientes
                )
                
                # Determinar ID del cliente
                if cliente_seleccionado == "Cuenta propia":
                    id_cliente = None
                else:
                    try:
                        id_cliente = st.session_state.clientes[opciones_clientes.index(cliente_seleccionado) - 1]['id']
                    except:
                        id_cliente = None
            else:
                st.warning("No se encontraron clientes")
                id_cliente = None
            
            # Botón de cerrar sesión
            if st.button("🚪 Cerrar Sesión"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Contenido principal
    if st.session_state.token_acceso is None:
        st.info("👈 Por favor, inicie sesión en la barra lateral para continuar")
        
        # Mostrar información de la aplicación
        st.markdown("""
        ## 🎯 Características Principales
        
        - **📊 Análisis de Portafolio**: Visualización detallada de activos y composición
        - **💰 Estado de Cuenta**: Resumen completo de posiciones y saldos
        - **🔄 Optimización**: Herramientas de análisis de portafolio (en desarrollo)
        - **💱 Cotizaciones**: MEP y cotizaciones de mercado
        
        ## 🚀 Comenzar
        1. Ingrese sus credenciales de IOL en la barra lateral
        2. Seleccione el cliente a analizar
        3. Explore las diferentes pestañas de análisis
        """)
        
    else:
        # Pestañas principales
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Resumen",
            "💰 Estado Cuenta", 
            "🔄 Optimización",
            "💱 Mercado"
        ])
        
        with tab1:
            st.header("📊 Resumen del Portafolio")
            
            if id_cliente is not None:
                with st.spinner("Cargando portafolio..."):
                    portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
                
                if portafolio:
                    mostrar_resumen_portafolio(portafolio)
                else:
                    st.error("❌ No se pudo cargar el portafolio")
            else:
                st.info("Seleccione un cliente para ver el resumen del portafolio")
        
        with tab2:
            st.header("💰 Estado de Cuenta")
            
            with st.spinner("Cargando estado de cuenta..."):
                estado_cuenta = obtener_estado_cuenta(st.session_state.token_acceso, id_cliente)
            
            if estado_cuenta:
                mostrar_estado_cuenta(estado_cuenta)
            else:
                st.error("❌ No se pudo cargar el estado de cuenta")
        
        with tab3:
            st.header("🔄 Optimización de Portafolio")
            
            if id_cliente is not None:
                mostrar_optimizacion_portafolio(st.session_state.token_acceso, id_cliente)
            else:
                st.info("Seleccione un cliente para analizar el portafolio")
        
        with tab4:
            st.header("💱 Cotizaciones y Mercado")
            mostrar_cotizaciones_mercado(st.session_state.token_acceso)

# === EJECUTAR APLICACIÓN ===
if __name__ == "__main__":
    main()
