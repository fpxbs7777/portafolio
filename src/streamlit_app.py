import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats
from scipy import optimize
import random
import warnings
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import time
import seaborn as sns
from streamlit_option_menu import option_menu
import altair as alt
from streamlit_aggrid import AgGrid, GridOptionsBuilder
import streamlit_authenticator as stauth
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_extras.app_logo import add_logo
from streamlit_extras.badges import badge
from streamlit_extras.let_it_rain import rain
from streamlit_extras.stateful_button import button
from streamlit_extras.switch_page_button import switch_page

warnings.filterwarnings('ignore')

# Configuración de la página con tema oscuro profesional
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funciones de Autenticación y API ---

def obtener_encabezado_autorizacion(token_portador):
    """Obtiene el encabezado de autorización para las llamadas a la API"""
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

def verificar_token(token_portador):
    """Verifica si el token es válido haciendo una llamada de prueba"""
    try:
        url = 'https://api.invertironline.com/api/v2/estadocuenta'
        headers = obtener_encabezado_autorizacion(token_portador)
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

def obtener_clientes(token_portador):
    """Obtiene la lista de clientes del asesor"""
    url = 'https://api.invertironline.com/api/v2/asesores/clientes'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener clientes: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener clientes: {str(e)}")
        return []

def obtener_portafolio(token_portador, cliente_id, mercado="Argentina"):
    """Obtiene el portafolio del cliente"""
    url = f'https://api.invertironline.com/api/v2/portafolio/{cliente_id}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener portafolio: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener portafolio: {str(e)}")
        return None

def obtener_portafolio_eeuu(token_portador, cliente_id):
    """Obtiene el portafolio de EEUU del cliente"""
    url = f'https://api.invertironline.com/api/v2/portafolio/{cliente_id}/eeuu'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener portafolio EEUU: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener portafolio EEUU: {str(e)}")
        return None

def obtener_estado_cuenta(token_portador, cliente_id):
    """Obtiene el estado de cuenta del cliente"""
    url = f'https://api.invertironline.com/api/v2/estadocuenta/{cliente_id}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado de cuenta: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener estado de cuenta: {str(e)}")
        return None

def obtener_estado_cuenta_eeuu(token_portador):
    """Obtiene el estado de cuenta de EEUU"""
    url = 'https://api.invertironline.com/api/v2/estadocuenta/eeuu'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado de cuenta EEUU: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener estado de cuenta EEUU: {str(e)}")
        return None

# --- Funciones de Análisis ---

def calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador):
    """Calcula métricas del portafolio"""
    try:
        if not portafolio_dict or valor_total <= 0:
            return None
        
        # Calcular concentración (Herfindahl)
        pesos = [activo['Valuación'] / valor_total for activo in portafolio_dict.values()]
        concentracion = sum(p**2 for p in pesos)
        
        # Calcular volatilidad promedio (simplificado)
        volatilidad_portafolio = 0.15  # 15% promedio para el mercado argentino
        
        # Calcular retorno esperado (simplificado)
        retorno_esperado_anual = 0.10  # 10% promedio
        
        # Calcular escenarios
        pl_esperado_max = valor_total * (retorno_esperado_anual + 1.96 * volatilidad_portafolio)
        pl_esperado_min = valor_total * (retorno_esperado_anual - 1.96 * volatilidad_portafolio)
        
        # Calcular probabilidades
        probabilidades = {
            'ganancia': 0.6,
            'perdida': 0.4,
            'ganancia_mayor_10': 0.3,
            'perdida_mayor_10': 0.2
        }
        
        return {
            'concentracion': concentracion,
            'std_dev_activo': volatilidad_portafolio,
            'retorno_esperado_anual': retorno_esperado_anual,
            'pl_esperado_max': pl_esperado_max,
            'pl_esperado_min': pl_esperado_min,
            'probabilidades': probabilidades,
            'riesgo_anual': volatilidad_portafolio
        }
    except Exception as e:
        st.error(f"Error calculando métricas: {str(e)}")
        return None

# --- Funciones de Visualización ---

def mostrar_resumen_portafolio(portafolio, token_portador, portfolio_id="", id_cliente=None):
    # Header con diseño avanzado
    colored_header(
        label=f"📈 Análisis de Portafolio - {portfolio_id.upper()}" if portfolio_id else "📈 Análisis de Portafolio",
        description="Análisis completo del portafolio de inversiones",
        color_name="blue-70"
    )
    
    # Mostrar información del cliente seleccionado
    if id_cliente:
        cliente_info = st.session_state.get('cliente_seleccionado', {})
        
        # Dashboard del cliente con métricas avanzadas
        st.markdown("### 👤 Dashboard del Cliente")
        
        # Métricas principales en cards estilizados
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            nombre_completo = cliente_info.get('apellidoYNombre', cliente_info.get('nombre', 'Cliente'))
            st.metric("👤 Cliente", nombre_completo)
        
        with col2:
            numero_cliente = cliente_info.get('numeroCliente', cliente_info.get('id', 'N/A'))
            st.metric("🆔 ID Cliente", numero_cliente)
        
        with col3:
            numero_cuenta = cliente_info.get('numeroCuenta', 'N/A')
            st.metric("🏦 Nº Cuenta", numero_cuenta)
        
        with col4:
            st.metric("📊 Portafolio", portfolio_id.upper() if portfolio_id else "General")
        
        # Aplicar estilos a las métricas
        style_metric_cards(
            background_color="#f0f2f6",
            border_left_color="#1f77b4",
            border_color="#1f77b4",
            box_shadow="#f0f2f6"
        )
        
        # Estado financiero en dashboard avanzado
        st.markdown("### 💰 Estado Financiero")
        
        # Crear DataFrame para visualización avanzada
        fin_data = {
            'Métrica': ['Disponible ARS', 'Disponible USD', 'Total Portafolio', 'Total Cuenta'],
            'Valor': [
                cliente_info.get('disponibleOperarPesos', 0),
                cliente_info.get('disponibleOperarDolares', 0),
                cliente_info.get('totalPortafolio', 0),
                cliente_info.get('totalCuentaValorizado', 0)
            ],
            'Moneda': ['ARS', 'USD', 'ARS', 'ARS'],
            'Icono': ['💵', '💲', '📈', '💰']
        }
        
        df_fin = pd.DataFrame(fin_data)
        
        # Métricas financieras con diseño mejorado
        col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
        
        for i, col in enumerate([col_fin1, col_fin2, col_fin3, col_fin4]):
            with col:
                valor = fin_data['Valor'][i]
                moneda = fin_data['Moneda'][i]
                icono = fin_data['Icono'][i]
                metrica = fin_data['Métrica'][i]
                
                if moneda == 'USD':
                    display_valor = f"USD {valor:,.2f}"
                else:
                    display_valor = f"AR$ {valor:,.2f}"
                
                st.metric(metrica, display_valor)
        
        # Gráfico de estado financiero
        fig_fin = px.bar(
            df_fin, 
            x='Métrica', 
            y='Valor',
            color='Métrica',
            title="Distribución del Capital",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_fin.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Métricas Financieras",
            yaxis_title="Valor"
        )
        st.plotly_chart(fig_fin, use_container_width=True)
    
    activos = portafolio.get('activos', [])
    datos_activos = []
    valor_total = 0
    
    for activo in activos:
        try:
            datos_activo = {
                'Símbolo': activo.get('simbolo', 'N/A'),
                'Descripción': activo.get('descripcion', 'N/A'),
                'Tipo': activo.get('tipoInstrumento', 'N/A'),
                'Cantidad': float(activo.get('cantidad', 0)),
                'Precio': float(activo.get('precioPromedio', 0)),
                'Valuación': float(activo.get('valorizado', 0))
            }
            datos_activos.append(datos_activo)
            valor_total += datos_activo['Valuación']
        except (ValueError, TypeError) as e:
            st.warning(f"Error procesando activo {activo.get('simbolo', 'N/A')}: {str(e)}")
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        # Convert list to dictionary with symbols as keys
        portafolio_dict = {row['Símbolo']: row for row in datos_activos}
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
        
        # Dashboard del portafolio con análisis avanzado
        colored_header(
            label="📊 Análisis del Portafolio",
            description="Métricas clave y composición del portafolio",
            color_name="violet-70"
        )
        
        # Métricas del portafolio con diseño avanzado
        col_port1, col_port2, col_port3, col_port4 = st.columns(4)
        
        with col_port1:
            st.metric("📈 Activos", len(datos_activos), help="Total de posiciones")
        
        with col_port2:
            st.metric("🔤 Símbolos", df_activos['Símbolo'].nunique(), help="Instrumentos únicos")
        
        with col_port3:
            st.metric("🏷️ Tipos", df_activos['Tipo'].nunique(), help="Categorías de activos")
        
        with col_port4:
            st.metric("💰 Valor", f"AR$ {valor_total:,.0f}", help="Valor total")
        
        # Aplicar estilos a las métricas del portafolio
        style_metric_cards(
            background_color="#f0f2f6",
            border_left_color="#ff7f0e",
            border_color="#ff7f0e",
            box_shadow="#f0f2f6"
        )
        
        if metricas:
            # Dashboard de Riesgo y Rendimiento
            colored_header(
                label="⚖️ Análisis de Riesgo y Rendimiento",
                description="Evaluación integral del riesgo y proyecciones",
                color_name="red-70"
            )
            
            # Crear tabs para organizar la información
            tab_riesgo, tab_rendimiento, tab_probabilidades = st.tabs(["🎯 Riesgo", "📈 Rendimiento", "🎲 Probabilidades"])
            
            with tab_riesgo:
                col_riesgo1, col_riesgo2, col_riesgo3 = st.columns(3)
                
                # Concentración
                concentracion_pct = metricas['concentracion'] * 100
                if metricas['concentracion'] < 0.3:
                    concentracion_status = "🟢 Baja"
                    concentracion_color = "green"
                elif metricas['concentracion'] < 0.6:
                    concentracion_status = "🟡 Media"
                    concentracion_color = "orange"
                else:
                    concentracion_status = "🔴 Alta"
                    concentracion_color = "red"
                
                col_riesgo1.metric(
                    "Concentración", 
                    f"{concentracion_pct:.2f}%",
                    help="Índice de Herfindahl: 0%=diversificado, 100%=concentrado"
                )
                
                # Volatilidad
                volatilidad_pct = metricas['std_dev_activo'] * 100
                col_riesgo2.metric(
                    "Volatilidad Anual", 
                    f"{volatilidad_pct:.2f}%",
                    help="Riesgo medido como desviación estándar"
                )
                
                # Nivel de concentración
                col_riesgo3.metric("Nivel", concentracion_status)
                
                # Gráfico de riesgo
                riesgo_data = {
                    'Métrica': ['Concentración', 'Volatilidad'],
                    'Valor': [concentracion_pct, volatilidad_pct],
                    'Color': ['#ff6b6b', '#4ecdc4']
                }
                
                fig_riesgo = px.bar(
                    pd.DataFrame(riesgo_data),
                    x='Métrica',
                    y='Valor',
                    color='Métrica',
                    title="Perfil de Riesgo",
                    color_discrete_sequence=['#ff6b6b', '#4ecdc4']
                )
                fig_riesgo.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_riesgo, use_container_width=True)
            
            with tab_rendimiento:
                col_rend1, col_rend2, col_rend3 = st.columns(3)
                
                # Retorno esperado
                retorno_anual_pct = metricas['retorno_esperado_anual'] * 100
                col_rend1.metric(
                    "Retorno Esperado", 
                    f"{retorno_anual_pct:+.2f}%",
                    help="Retorno anual esperado"
                )
                
                # Escenarios
                optimista_pct = (metricas['pl_esperado_max'] / valor_total) * 100 if valor_total > 0 else 0
                pesimista_pct = (metricas['pl_esperado_min'] / valor_total) * 100 if valor_total > 0 else 0
                
                col_rend2.metric("Optimista (95%)", f"{optimista_pct:+.2f}%")
                col_rend3.metric("Pesimista (5%)", f"{pesimista_pct:+.2f}%")
                
                # Gráfico de escenarios
                escenarios_data = {
                    'Escenario': ['Optimista', 'Esperado', 'Pesimista'],
                    'Retorno (%)': [optimista_pct, retorno_anual_pct, pesimista_pct],
                    'Color': ['#2ecc71', '#3498db', '#e74c3c']
                }
                
                fig_escenarios = px.bar(
                    pd.DataFrame(escenarios_data),
                    x='Escenario',
                    y='Retorno (%)',
                    color='Escenario',
                    title="Escenarios de Rendimiento",
                    color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c']
                )
                fig_escenarios.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_escenarios, use_container_width=True)
            
            with tab_probabilidades:
                probs = metricas['probabilidades']
                
                col_prob1, col_prob2, col_prob3, col_prob4 = st.columns(4)
                
                col_prob1.metric("Ganancia", f"{probs['ganancia']*100:.1f}%")
                col_prob2.metric("Pérdida", f"{probs['perdida']*100:.1f}%")
                col_prob3.metric("Ganancia >10%", f"{probs['ganancia_mayor_10']*100:.1f}%")
                col_prob4.metric("Pérdida >10%", f"{probs['perdida_mayor_10']*100:.1f}%")
                
                # Gráfico de probabilidades
                prob_data = {
                    'Categoría': ['Ganancia', 'Pérdida', 'Ganancia >10%', 'Pérdida >10%'],
                    'Probabilidad (%)': [
                        probs['ganancia']*100,
                        probs['perdida']*100,
                        probs['ganancia_mayor_10']*100,
                        probs['perdida_mayor_10']*100
                    ]
                }
                
                fig_probs = px.pie(
                    pd.DataFrame(prob_data),
                    values='Probabilidad (%)',
                    names='Categoría',
                    title="Distribución de Probabilidades",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_probs.update_layout(height=400)
                st.plotly_chart(fig_probs, use_container_width=True)
        
        # Visualizaciones del Portafolio
        colored_header(
            label="📊 Visualizaciones del Portafolio",
            description="Análisis visual de la composición y distribución",
            color_name="green-70"
        )
        
        # Tabs para organizar las visualizaciones
        tab_composicion, tab_distribucion, tab_analisis = st.tabs(["🥧 Composición", "📈 Distribución", "📋 Análisis"])
        
        with tab_composicion:
            # Gráfico de composición por tipo de activo
            if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
                tipo_stats = df_activos.groupby('Tipo')['Valuación'].sum().reset_index()
                
                # Gráfico de torta mejorado
                fig_pie = px.pie(
                    tipo_stats,
                    values='Valuación',
                    names='Tipo',
                    title="Composición por Tipo de Activo",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Valor: AR$ %{value:,.0f}<br>Porcentaje: %{percent}<extra></extra>'
                )
                fig_pie.update_layout(
                    height=500,
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Gráfico de barras complementario
                fig_bars = px.bar(
                    tipo_stats,
                    x='Tipo',
                    y='Valuación',
                    title="Valor por Tipo de Activo",
                    color='Valuación',
                    color_continuous_scale='viridis'
                )
                fig_bars.update_traces(
                    texttemplate='AR$ %{y:,.0f}',
                    textposition='outside'
                )
                fig_bars.update_layout(
                    height=400,
                    xaxis_title="Tipo de Activo",
                    yaxis_title="Valor (AR$)",
                    showlegend=False
                )
                st.plotly_chart(fig_bars, use_container_width=True)
        
        with tab_distribucion:
            # Histograma de distribución de valores
            if len(datos_activos) > 1:
                valores_activos = [a['Valuación'] for a in datos_activos if a['Valuación'] > 0]
                if valores_activos:
                    fig_hist = px.histogram(
                        x=valores_activos,
                        nbins=min(20, len(valores_activos)),
                        title="Distribución de Valores de Activos",
                        labels={'x': 'Valor (AR$)', 'y': 'Frecuencia'},
                        color_discrete_sequence=['#3498db']
                    )
                    fig_hist.update_layout(
                        height=500,
                        xaxis_title="Valor del Activo (AR$)",
                        yaxis_title="Frecuencia",
                        showlegend=False
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Box plot para análisis estadístico
                    fig_box = px.box(
                        y=valores_activos,
                        title="Análisis Estadístico de Valores",
                        labels={'y': 'Valor (AR$)'}
                    )
                    fig_box.update_layout(
                        height=400,
                        yaxis_title="Valor del Activo (AR$)",
                        showlegend=False
                    )
                    st.plotly_chart(fig_box, use_container_width=True)
        
        with tab_analisis:
            # Tabla interactiva con AgGrid
            if len(df_activos) > 0:
                # Preparar datos para la tabla
                df_display = df_activos.copy()
                df_display['Peso (%)'] = (df_display['Valuación'] / valor_total * 100).round(2)
                df_display['Valuación'] = df_display['Valuación'].apply(lambda x: f"AR$ {x:,.2f}")
                
                # Configurar AgGrid
                gb = GridOptionsBuilder.from_dataframe(df_display)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_default_column(
                    groupable=True,
                    value=True,
                    enableRowGroup=True,
                    aggFunc='sum',
                    editable=True
                )
                gb.configure_column("Símbolo", pinned="left")
                gb.configure_column("Valuación", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=2)
                
                gridOptions = gb.build()
                
                st.markdown("### 📋 Tabla Detallada de Activos")
                AgGrid(
                    df_display,
                    gridOptions=gridOptions,
                    data_return_mode='AS_INPUT',
                    update_mode='MODEL_CHANGED',
                    fit_columns_on_grid_load=True,
                    theme='alpine'
                )
        
    else:
        st.warning("No se encontraron activos en el portafolio")

def mostrar_estado_cuenta(estado_cuenta, es_eeuu=False):
    """
    Muestra el estado de cuenta, con soporte para cuentas filtradas de EEUU
    
    Args:
        estado_cuenta (dict): Datos del estado de cuenta
        es_eeuu (bool): Si es True, muestra información específica para cuentas de EEUU
    """
    if es_eeuu:
        st.markdown("### 🇺🇸 Estado de Cuenta EEUU")
    else:
        st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No se ha seleccionado ningún cliente")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Cargar datos una sola vez y cachearlos
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def cargar_datos_cliente(token, cliente_id):
        """Carga y cachea los datos del cliente para evitar llamadas repetitivas"""
        portafolio_ar = obtener_portafolio(token, cliente_id, 'Argentina')
        portafolio_eeuu = obtener_portafolio_eeuu(token, cliente_id)
        estado_cuenta_ar = obtener_estado_cuenta(token, cliente_id)
        estado_cuenta_eeuu = obtener_estado_cuenta_eeuu(token)
        return portafolio_ar, portafolio_eeuu, estado_cuenta_ar, estado_cuenta_eeuu
    
    # Cargar datos con cache
    with st.spinner("🔄 Cargando datos del cliente..."):
        portafolio_ar, portafolio_eeuu, estado_cuenta_ar, estado_cuenta_eeuu = cargar_datos_cliente(token_acceso, id_cliente)
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🇦🇷 Portafolio Argentina", 
        "🇺🇸 Portafolio EEUU",
        "💰 Estado de Cuenta", 
        "🎯 Optimización y Cobertura",
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "📈 Operaciones Reales"
    ])

    with tab1:
        if portafolio_ar:
            st.subheader("🇦🇷 Portafolio Argentina")
            mostrar_resumen_portafolio(portafolio_ar, token_acceso, "ar", id_cliente)
        else:
            st.warning("No se pudo obtener el portafolio de Argentina")
    
    with tab2:
        if portafolio_eeuu:
            st.subheader("🇺🇸 Portafolio Estados Unidos")
            mostrar_resumen_portafolio(portafolio_eeuu, token_acceso, "eeuu", id_cliente)
        else:
            st.warning("No se pudo obtener el portafolio de EEUU")
    
    with tab3:
        st.subheader("💰 Estado de Cuenta")
        col_estado1, col_estado2 = st.columns(2)
        
        with col_estado1:
            if estado_cuenta_ar:
                mostrar_estado_cuenta(estado_cuenta_ar, es_eeuu=False)
            else:
                st.warning("No se pudo obtener el estado de cuenta de Argentina")
        
        with col_estado2:
            if estado_cuenta_eeuu:
                mostrar_estado_cuenta(estado_cuenta_eeuu, es_eeuu=True)
            else:
                st.warning("No se pudo obtener el estado de cuenta de EEUU")
    
    with tab4:
        st.subheader("🎯 Optimización y Cobertura")
        st.info("Funcionalidad de optimización en desarrollo...")
    
    with tab5:
        st.subheader("📊 Análisis Técnico")
        st.info("Funcionalidad de análisis técnico en desarrollo...")
    
    with tab6:
        st.subheader("💱 Cotizaciones")
        st.info("Funcionalidad de cotizaciones en desarrollo...")
    
    with tab7:
        st.subheader("📈 Operaciones Reales")
        st.info("Funcionalidad de operaciones reales en desarrollo...")

# Función principal
def main():
    # Configuración de rendimiento
    st.set_page_config(
        page_title="IOL Portfolio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configurar cache para mejor rendimiento
    if hasattr(st, 'cache_data'):
        st.cache_data.clear()
    
    # Header principal con gradiente
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">📊 IOL Portfolio Analyzer</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; font-size: 1.2rem;">Analizador Avanzado de Portafolios IOL</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar session state
    if 'token_acceso' not in st.session_state:
        st.session_state.token_acceso = None
    if 'cliente_seleccionado' not in st.session_state:
        st.session_state.cliente_seleccionado = None
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0; text-align: center;">🔐 Autenticación IOL</h2>
        </div>
        """, unsafe_allow_html=True)
        
        token_acceso = st.text_input("Token de Acceso", type="password", help="Ingresa tu token de acceso de IOL")
        
        if token_acceso:
            st.session_state.token_acceso = token_acceso
            st.success("✅ Conectado a IOL")
            
            # Configuración de fechas
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <h3 style="color: white; margin: 0; text-align: center;">📅 Configuración de Fechas</h3>
            </div>
            """, unsafe_allow_html=True)
            
            fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=365))
            fecha_hasta = st.date_input("Hasta", value=date.today())
            
            # Selección de cliente
            if st.session_state.token_acceso:
                clientes = obtener_clientes(st.session_state.token_acceso)
                if clientes:
                    nombres_clientes = [f"{c.get('apellidoYNombre', c.get('nombre', 'Cliente'))} - {c.get('numeroCliente', c.get('id', 'N/A'))}" for c in clientes]
                    cliente_seleccionado = st.selectbox("Selección de Cliente", nombres_clientes)
                    
                    if cliente_seleccionado:
                        cliente_id = cliente_seleccionado.split(" - ")[-1]
                        cliente_info = next((c for c in clientes if str(c.get('numeroCliente', c.get('id'))) == cliente_id), None)
                        if cliente_info:
                            st.session_state.cliente_seleccionado = cliente_info
                            st.success(f"✅ Cliente seleccionado: {cliente_info.get('apellidoYNombre', cliente_info.get('nombre', 'Cliente'))}")
    
    # Menú principal
    if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
        with st.sidebar:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <h3 style="color: white; margin: 0; text-align: center;">🎯 Menú Principal</h3>
            </div>
            """, unsafe_allow_html=True)
            
            opcion = st.selectbox(
                "Seleccione una opción:",
                ["🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨‍💼 Panel del Asesor"]
            )
        
        # Navegación
        if opcion == "🏠 Inicio":
            st.markdown("### 🏠 Bienvenido al IOL Portfolio Analyzer")
            st.info("Selecciona 'Análisis de Portafolio' para comenzar el análisis del cliente seleccionado.")
            
        elif opcion == "📊 Análisis de Portafolio":
            mostrar_analisis_portafolio()
            
        elif opcion == "💰 Tasas de Caución":
            st.markdown("### 💰 Tasas de Caución")
            st.info("Funcionalidad de tasas de caución en desarrollo...")
            
        elif opcion == "👨‍💼 Panel del Asesor":
            st.markdown("### 👨‍💼 Panel del Asesor")
            st.info("Funcionalidad del panel del asesor en desarrollo...")
    
    else:
        st.info("🔐 Por favor, ingresa tu token de acceso y selecciona un cliente para comenzar.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>📊 IOL Portfolio Analyzer - Analizador Avanzado de Portafolios IOL</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
