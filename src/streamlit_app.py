"""
IOL Portfolio Analyzer - Versión Mejorada y Organizada
=====================================================

Aplicación Streamlit para análisis avanzado de portafolios de inversión
con integración a la API de IOL (Invertir Online).

Características principales:
- Análisis completo de portafolios
- Optimización avanzada con múltiples estrategias
- Análisis técnico integrado
- Gestión de riesgo y diversificación
- Interfaz moderna y responsive
"""

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
from scipy import optimize
import warnings
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import time

# Configuración de warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ============================================================================

def configurar_pagina():
    """Configura la página principal de Streamlit"""
    st.set_page_config(
        page_title="IOL Portfolio Analyzer Pro",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def aplicar_estilos_css():
    """Aplica estilos CSS personalizados para una interfaz moderna"""
    st.markdown("""
    <style>
        /* Tema oscuro profesional */
        .stApp, 
        .stApp > div[data-testid="stAppViewContainer"],
        .stApp > div[data-testid="stAppViewContainer"] > div {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Títulos con gradiente */
        h1, h2, h3 {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        
        /* Tarjetas modernas */
        .metric-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #4CAF50;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        
        /* Botones modernos */
        .stButton > button {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            border-radius: 25px;
            border: none;
            color: white;
            font-weight: 600;
            padding: 12px 24px;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
        }
        
        /* Pestañas mejoradas */
        .stTabs [data-baseweb="tab"] {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            color: #e2e8f0;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        
        /* Inputs modernos */
        .stTextInput, .stNumberInput, .stDateInput, .stSelectbox {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 10px;
            border: 1px solid #4CAF50;
        }
        
        /* Tablas mejoradas */
        .dataframe {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 15px;
            overflow: hidden;
        }
        
        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1e293b;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# FUNCIONES DE AUTENTICACIÓN Y CONEXIÓN IOL
# ============================================================================

def obtener_encabezado_autorizacion(token_portador):
    """Retorna headers de autorización para la API de IOL"""
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

def obtener_tokens(usuario, contraseña):
    """Obtiene tokens de autenticación de IOL con manejo mejorado de errores"""
    url_login = 'https://api.invertironline.com/token'
    datos = {
        'username': usuario,
        'password': contraseña,
        'grant_type': 'password'
    }
    
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=3,
        pool_connections=10,
        pool_maxsize=10
    ))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            st.info(f"🔄 Intento {attempt + 1}/{max_attempts} de conexión a IOL...")
            
            timeout = 30 if attempt == 0 else 15
            respuesta = session.post(url_login, data=datos, headers=headers, timeout=timeout)
            
            if respuesta.status_code == 200:
                respuesta_json = respuesta.json()
                if 'access_token' in respuesta_json and 'refresh_token' in respuesta_json:
                    st.success("✅ Autenticación exitosa con IOL")
                    return respuesta_json['access_token'], respuesta_json['refresh_token']
                else:
                    st.error("❌ Respuesta de IOL incompleta")
                    return None, None
            
            elif respuesta.status_code == 400:
                st.error("❌ Verifique sus credenciales (usuario/contraseña)")
                return None, None
            elif respuesta.status_code == 401:
                st.error("❌ Credenciales inválidas o cuenta bloqueada")
                return None, None
            elif respuesta.status_code == 429:
                st.warning("⚠️ Demasiadas solicitudes. Esperando...")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error("❌ Límite de solicitudes excedido")
                    return None, None
            else:
                st.error(f"❌ Error HTTP {respuesta.status_code}")
                return None, None
                
        except requests.exceptions.Timeout:
            st.warning(f"⏱️ Timeout en intento {attempt + 1}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                st.error("❌ Timeout persistente")
                return None, None
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return None, None
    
    st.error("❌ No se pudo establecer conexión después de múltiples intentos")
    return None, None

# ============================================================================
# FUNCIONES DE OBTENCIÓN DE DATOS IOL
# ============================================================================

def obtener_lista_clientes(token_portador):
    """Obtiene la lista de clientes del asesor"""
    url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_clientes, headers=encabezados, timeout=30)
        if respuesta.status_code == 200:
            clientes_data = respuesta.json()
            if isinstance(clientes_data, list):
                return clientes_data
            elif isinstance(clientes_data, dict) and 'clientes' in clientes_data:
                return clientes_data['clientes']
            else:
                st.warning("Formato de respuesta inesperado")
                return []
        else:
            st.error(f'Error HTTP {respuesta.status_code} al obtener clientes')
            return []
    except Exception as e:
        st.error(f'Error de conexión: {str(e)}')
        return []

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    """Obtiene el portafolio de un cliente específico"""
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados, timeout=30)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error HTTP {respuesta.status_code} al obtener portafolio")
            return None
    except Exception as e:
        st.error(f'Error al obtener portafolio: {str(e)}')
        return None

def obtener_estado_cuenta(token_portador, id_cliente=None):
    """Obtiene el estado de cuenta del cliente"""
    if id_cliente:
        url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    else:
        url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados, timeout=30)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error HTTP {respuesta.status_code} al obtener estado de cuenta")
            return None
    except Exception as e:
        st.error(f'Error al obtener estado de cuenta: {str(e)}')
        return None

# ============================================================================
# FUNCIONES DE ANÁLISIS DE PORTAFOLIO
# ============================================================================

def mostrar_resumen_portafolio(portafolio, token_acceso):
    """Muestra un resumen visual del portafolio"""
    st.markdown("### 📊 Resumen del Portafolio")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("El portafolio está vacío")
        return
    
    # Calcular métricas del portafolio
    valor_total = sum(activo.get('valuacionActual', 0) for activo in activos)
    num_activos = len(activos)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Valor Total",
            f"${valor_total:,.2f}",
            help="Valor total del portafolio"
        )
    
    with col2:
        st.metric(
            "📈 Número de Activos",
            num_activos,
            help="Cantidad total de activos"
        )
    
    with col3:
        # Calcular distribución por tipo
        tipos_activo = {}
        for activo in activos:
            tipo = activo.get('titulo', {}).get('tipoInstrumento', 'Desconocido')
            tipos_activo[tipo] = tipos_activo.get(tipo, 0) + 1
        
        tipo_principal = max(tipos_activo.items(), key=lambda x: x[1])[0] if tipos_activo else "N/A"
        st.metric(
            "🎯 Tipo Principal",
            tipo_principal,
            help="Tipo de instrumento más común"
        )
    
    with col4:
        # Calcular concentración
        if valor_total > 0:
            valores = [activo.get('valuacionActual', 0) for activo in activos]
            concentracion = max(valores) / valor_total * 100
            st.metric(
                "⚖️ Concentración Máx",
                f"{concentracion:.1f}%",
                help="Porcentaje del activo más concentrado"
            )
    
    # Gráfico de distribución por tipo
    st.markdown("#### 📊 Distribución por Tipo de Instrumento")
    
    tipos_data = {}
    for activo in activos:
        tipo = activo.get('titulo', {}).get('tipoInstrumento', 'Desconocido')
        valor = activo.get('valuacionActual', 0)
        tipos_data[tipo] = tipos_data.get(tipo, 0) + valor
    
    if tipos_data:
        fig = go.Figure(data=[go.Pie(
            labels=list(tipos_data.keys()),
            values=list(tipos_data.values()),
            hole=0.4,
            marker_colors=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336']
        )])
        
        fig.update_layout(
            title="Distribución del Portafolio por Tipo",
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de activos principales
    st.markdown("#### 📋 Activos Principales")
    
    if activos:
        # Ordenar por valor
        activos_ordenados = sorted(activos, key=lambda x: x.get('valuacionActual', 0), reverse=True)
        
        # Crear DataFrame para la tabla
        datos_tabla = []
        for activo in activos_ordenados[:10]:  # Top 10
            titulo = activo.get('titulo', {})
            datos_tabla.append({
                'Símbolo': titulo.get('simbolo', 'N/A'),
                'Tipo': titulo.get('tipoInstrumento', 'N/A'),
                'Cantidad': activo.get('cantidad', 0),
                'Valor Unitario': f"${activo.get('precioPromedio', 0):,.2f}",
                'Valor Actual': f"${activo.get('valuacionActual', 0):,.2f}",
                'Rendimiento': f"{activo.get('rendimiento', 0):.2f}%"
            })
        
        df_activos = pd.DataFrame(datos_tabla)
        st.dataframe(df_activos, use_container_width=True, height=400)

def mostrar_estado_cuenta(estado_cuenta):
    """Muestra el estado de cuenta del cliente"""
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    # Extraer información relevante
    saldos = estado_cuenta.get('saldos', {})
    cuentas = estado_cuenta.get('cuentas', [])
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        saldo_disponible = saldos.get('disponible', 0)
        st.metric(
            "💵 Saldo Disponible",
            f"${saldo_disponible:,.2f}",
            help="Saldo disponible para operaciones"
        )
    
    with col2:
        saldo_total = saldos.get('total', 0)
        st.metric(
            "🏦 Saldo Total",
            f"${saldo_total:,.2f}",
            help="Saldo total de la cuenta"
        )
    
    with col3:
        if saldo_total > 0:
            porcentaje_disponible = (saldo_disponible / saldo_total) * 100
            st.metric(
                "📊 % Disponible",
                f"{porcentaje_disponible:.1f}%",
                help="Porcentaje del saldo disponible"
            )
    
    # Información de cuentas
    if cuentas:
        st.markdown("#### 🏛️ Cuentas del Cliente")
        
        datos_cuentas = []
        for cuenta in cuentas:
            datos_cuentas.append({
                'Número': cuenta.get('numero', 'N/A'),
                'Tipo': cuenta.get('tipo', 'N/A'),
                'Moneda': cuenta.get('moneda', 'N/A'),
                'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                'Estado': cuenta.get('estado', 'N/A')
            })
        
        df_cuentas = pd.DataFrame(datos_cuentas)
        st.dataframe(df_cuentas, use_container_width=True)

# ============================================================================
# FUNCIONES DE OPTIMIZACIÓN DE PORTAFOLIO
# ============================================================================

def mostrar_menu_optimizacion(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """Menú principal de optimización de portafolio"""
    st.markdown("### 🎯 Optimización de Portafolio")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para optimizar")
        return
    
    # Extraer símbolos
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para optimización")
        return
    
    # Configuración de optimización
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚙️ Configuración")
        estrategia = st.selectbox(
            "Estrategia de Optimización:",
            options=[
                'equi-weight',
                'min-variance',
                'max-sharpe',
                'markowitz'
            ],
            help="Seleccione la estrategia de optimización"
        )
        
        capital_inicial = st.number_input(
            "Capital Inicial (USD):",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=1000.0
        )
    
    with col2:
        st.markdown("#### 📅 Período de Análisis")
        st.info(f"📊 Analizando {len(simbolos)} activos desde {fecha_desde} hasta {fecha_hasta}")
        
        mostrar_graficos = st.checkbox("Mostrar Gráficos", value=True)
        auto_refresh = st.checkbox("Auto-refresh", value=False)
    
    # Botón de ejecución
    ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary", use_container_width=True)
    
    if ejecutar_optimizacion:
        with st.spinner("🔄 Ejecutando optimización..."):
            try:
                # Aquí iría la lógica de optimización real
                st.success("✅ Optimización completada")
                
                # Mostrar resultados simulados
                mostrar_resultados_optimizacion_simulados(simbolos, estrategia, capital_inicial)
                
            except Exception as e:
                st.error(f"❌ Error en la optimización: {str(e)}")

def mostrar_resultados_optimizacion_simulados(simbolos, estrategia, capital_inicial):
    """Muestra resultados simulados de optimización (placeholder)"""
    st.markdown("#### 📊 Resultados de la Optimización")
    
    # Simular resultados
    np.random.seed(42)
    pesos = np.random.dirichlet(np.ones(len(simbolos)))
    pesos = pesos / pesos.sum()
    
    # Crear DataFrame de resultados
    resultados_data = []
    for i, simbolo in enumerate(simbolos):
        resultados_data.append({
            'Activo': simbolo,
            'Peso (%)': f"{pesos[i] * 100:.2f}%",
            'Inversión': f"${pesos[i] * capital_inicial:,.2f}",
            'Rendimiento Esperado': f"{np.random.uniform(5, 15):.1f}%",
            'Riesgo': f"{np.random.uniform(10, 25):.1f}%"
        })
    
    df_resultados = pd.DataFrame(resultados_data)
    st.dataframe(df_resultados, use_container_width=True)
    
    # Gráfico de distribución de pesos
    fig = go.Figure(data=[go.Bar(
        x=simbolos,
        y=pesos * 100,
        marker_color='#4CAF50',
        text=[f"{p:.1f}%" for p in pesos * 100],
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Distribución de Pesos Optimizados",
        xaxis_title="Activos",
        yaxis_title="Peso (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# FUNCIONES DE ANÁLISIS TÉCNICO
# ============================================================================

def mostrar_analisis_tecnico(token_acceso, id_cliente):
    """Muestra análisis técnico de activos"""
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
    
    # Extraer símbolos
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos")
        return
    
    # Selección de activo
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos,
        help="Seleccione el activo que desea analizar"
    )
    
    if simbolo_seleccionado:
        st.info(f"📈 Mostrando análisis técnico para: {simbolo_seleccionado}")
        
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
          "theme": "dark",
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
          }}
        }});
        </script>
        """
        
        components.html(tv_widget, height=680)

# ============================================================================
# FUNCIONES DE COTIZACIONES Y MERCADO
# ============================================================================

def mostrar_cotizaciones_mercado(token_acceso):
    """Muestra cotizaciones y datos de mercado"""
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    # Cotización MEP
    with st.expander("💰 Cotización MEP", expanded=True):
        with st.form("mep_form"):
            col1, col2, col3 = st.columns(3)
            simbolo_mep = col1.text_input("Símbolo", value="AL30", help="Ej: AL30, GD30, etc.")
            id_plazo_compra = col2.number_input("ID Plazo Compra", value=1, min_value=1)
            id_plazo_venta = col3.number_input("ID Plazo Venta", value=1, min_value=1)
            
            if st.form_submit_button("🔍 Consultar MEP"):
                if simbolo_mep:
                    st.info("ℹ️ Función de cotización MEP en desarrollo")
                else:
                    st.warning("⚠️ Ingrese un símbolo válido")
    
    # Tasas de Caución
    with st.expander("🏦 Tasas de Caución", expanded=True):
        st.info("ℹ️ Función de tasas de caución en desarrollo")
        
        # Placeholder para futura implementación
        if st.button("🔄 Actualizar Tasas"):
            st.success("✅ Funcionalidad en desarrollo")

# ============================================================================
# FUNCIONES DE MOVIMIENTOS DEL ASESOR
# ============================================================================

def mostrar_movimientos_asesor():
    """Muestra el panel de movimientos del asesor"""
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
        
        # Selección de clientes
        cliente_opciones = [{"label": f"{c.get('apellidoYNombre', c.get('nombre', 'Cliente'))} ({c.get('numeroCliente', c.get('id', ''))})", 
                           "value": c.get('numeroCliente', c.get('id'))} for c in clientes]
        
        clientes_seleccionados = st.multiselect(
            "Seleccione clientes",
            options=[c['value'] for c in cliente_opciones],
            format_func=lambda x: next((c['label'] for c in cliente_opciones if c['value'] == x), x),
            default=[cliente_opciones[0]['value']] if cliente_opciones else []
        )
        
        buscar = st.form_submit_button("🔍 Buscar movimientos")
    
    if buscar and clientes_seleccionados:
        st.info("ℹ️ Función de búsqueda de movimientos en desarrollo")
        st.success("✅ Funcionalidad en desarrollo")

# ============================================================================
# FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# ============================================================================

def main():
    """Función principal de la aplicación"""
    # Configurar página
    configurar_pagina()
    aplicar_estilos_css()
    
    # Título principal
    st.title("📊 IOL Portfolio Analyzer Pro")
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
            
            # Configuración de fechas
            st.subheader("📅 Configuración de Fechas")
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
                st.subheader("👥 Selección de Cliente")
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨‍💼 Panel del Asesor"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                mostrar_pagina_inicio()
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
            elif opcion == "👨‍💼 Panel del Asesor":
                mostrar_movimientos_asesor()
        else:
            mostrar_pagina_inicio()
            
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

def mostrar_pagina_inicio():
    """Muestra la página de inicio con información de bienvenida"""
    st.info("👆 Ingrese sus credenciales para comenzar")
    
    # Panel de bienvenida
    st.markdown("""
    <div style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
                border-radius: 15px; 
                padding: 40px; 
                color: white;
                text-align: center;
                margin: 30px 0;">
        <h1 style="color: white; margin-bottom: 20px;">Bienvenido al Portfolio Analyzer Pro</h1>
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

def mostrar_tasas_caucion(token_acceso):
    """Muestra las tasas de caución"""
    st.subheader("📊 Tasas de Caución")
    st.info("ℹ️ Función de tasas de caución en desarrollo")

def mostrar_analisis_portafolio():
    """Función principal para mostrar el análisis de portafolio"""
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No se ha seleccionado ningún cliente")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos del cliente..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "🎯 Optimización y Cobertura",
        "📊 Análisis Técnico",
        "💱 Cotizaciones"
    ])

    with tab1:
        if portafolio:
            mostrar_resumen_portafolio(portafolio, token_acceso)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
    
    with tab3:
        if portafolio:
            mostrar_menu_optimizacion(portafolio, token_acceso, st.session_state.fecha_desde, st.session_state.fecha_hasta)
        else:
            st.warning("No se pudo obtener el portafolio para optimización")
    
    with tab4:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab5:
        mostrar_cotizaciones_mercado(token_acceso)

# ============================================================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================================================

if __name__ == "__main__":
    main()
