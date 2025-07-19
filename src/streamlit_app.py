import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
import json
import os
import zipfile
import sqlite3
import tempfile
import io
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configurar pandas para mejor rendimiento
pd.options.mode.chained_assignment = None

# Diccionarios de mapeo para nombres descriptivos
FRECUENCIA_MAPPING = {
    'R/P1Y': 'Anual',
    'R/P6M': 'Semestral', 
    'R/P3M': 'Trimestral',
    'R/P1M': 'Mensual',
    'R/P1D': 'Diaria',
    'R/P1W': 'Semanal',
    'R/P1H': 'Horaria',
    'R/P1MIN': 'Por Minuto'
}

DATASET_MAPPING = {
    'sspm': 'Sistema de Cuentas Nacionales',
    'snic': 'Sistema Nacional de Información de Comercio',
    'obras': 'Obras Públicas',
    'turismo': 'Turismo',
    'bcra': 'Banco Central de la República Argentina',
    'siep': 'Sistema de Información de Empleo Público',
    'justicia': 'Ministerio de Justicia',
    'jgm': 'Jefatura de Gabinete de Ministros',
    'agroindustria': 'Ministerio de Agroindustria',
    'smn': 'Servicio Meteorológico Nacional',
    'modernizacion': 'Secretaría de Modernización',
    'salud': 'Ministerio de Salud',
    'energia': 'Secretaría de Energía',
    'defensa': 'Ministerio de Defensa',
    'sspre': 'Sistema de Seguridad Pública',
    'cultura': 'Ministerio de Cultura',
    'transporte': 'Ministerio de Transporte',
    'test_node': 'Datos de Prueba',
    'otros': 'Otros Datos'
}

def mapear_frecuencia(frecuencia):
    """Convierte códigos de frecuencia en nombres descriptivos"""
    return FRECUENCIA_MAPPING.get(frecuencia, frecuencia)

def mapear_dataset(dataset_id):
    """Convierte códigos de dataset en nombres descriptivos"""
    return DATASET_MAPPING.get(dataset_id, dataset_id)

def aplicar_mapeos_descriptivos(df):
    """Aplica mapeos descriptivos a un DataFrame"""
    if 'indice_tiempo_frecuencia' in df.columns:
        df['frecuencia_descriptiva'] = df['indice_tiempo_frecuencia'].map(mapear_frecuencia)
    
    if 'dataset_id' in df.columns:
        df['dataset_descriptivo'] = df['dataset_id'].map(mapear_dataset)
    
    return df

# Configuración de la página
st.set_page_config(
    page_title="📊 Datos Económicos Argentina - Ministerio de Economía",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URLs de los datos
DATA_URLS = {
    "valores_csv": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-valores-csv.zip",
    "metadatos_csv": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-metadatos.csv",
    "fuentes_csv": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-fuentes.csv",
    "sqlite": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-sqlite.zip"
}

@st.cache_data(ttl=3600)  # Cache por 1 hora
def descargar_y_procesar_datos():
    """Descarga y procesa todos los datos desde las APIs oficiales con optimizaciones de velocidad"""
    
    with st.spinner("🔄 Descargando y procesando datos económicos..."):
        try:
            # Crear directorio temporal para los datos
            temp_dir = tempfile.mkdtemp()
            
            # Configurar sesión de requests con optimizaciones
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Descargar metadatos y fuentes en paralelo
            st.info("📥 Descargando metadatos y fuentes...")
            
            # Usar ThreadPoolExecutor para descargas paralelas
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def download_file(url, filename):
                response = session.get(url, timeout=30)
                response.raise_for_status()
                return filename, response.content
            
            # Descargas paralelas
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(download_file, DATA_URLS["metadatos_csv"], "metadatos.csv"): "metadatos",
                    executor.submit(download_file, DATA_URLS["fuentes_csv"], "fuentes.csv"): "fuentes",
                    executor.submit(download_file, DATA_URLS["valores_csv"], "valores.zip"): "valores"
                }
                
                results = {}
                for future in as_completed(futures):
                    try:
                        filename, content = future.result()
                        results[futures[future]] = (filename, content)
                    except Exception as e:
                        st.error(f"Error descargando {futures[future]}: {e}")
                        return None
            
            # Procesar metadatos
            metadatos_content = results['metadatos'][1]
            metadatos_df = pd.read_csv(io.StringIO(metadatos_content.decode('utf-8')))
            
            # Procesar fuentes
            fuentes_content = results['fuentes'][1]
            fuentes_df = pd.read_csv(io.StringIO(fuentes_content.decode('utf-8')))
            
            # Procesar valores ZIP
            st.info("📥 Procesando valores de series...")
            valores_zip_path = os.path.join(temp_dir, "valores.zip")
            with open(valores_zip_path, 'wb') as f:
                f.write(results['valores'][1])
            
            # Extraer valores con optimización
            with zipfile.ZipFile(valores_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Buscar archivo CSV de valores
            valores_file = None
            for file in os.listdir(temp_dir):
                if file.endswith('.csv') and 'valores' in file.lower():
                    valores_file = os.path.join(temp_dir, file)
                    break
            
            if valores_file:
                # Optimizar lectura de CSV
                valores_df = pd.read_csv(
                    valores_file,
                    dtype={
                        'serie_id': 'category',
                        'valor': 'float64'
                    },
                    parse_dates=['indice_tiempo'],
                    date_parser=pd.to_datetime,
                    engine='c'
                )
            else:
                st.error("No se encontró el archivo de valores")
                return None
            
            # Optimizar procesamiento de metadatos
            st.info("⚡ Procesando metadatos...")
            index_df = metadatos_df[['serie_id', 'catalogo_id', 'dataset_id', 'distribucion_id', 'indice_tiempo_frecuencia']].copy()
            
            # Aplicar mapeos descriptivos
            index_df = aplicar_mapeos_descriptivos(index_df)
            
            # Optimizar datasets
            dataset_df = metadatos_df[['dataset_id', 'dataset_responsable', 'dataset_fuente', 'dataset_titulo']].drop_duplicates()
            dataset_df = aplicar_mapeos_descriptivos(dataset_df)
            
            # Optimizar distribución
            distribucion_df = metadatos_df[['distribucion_id', 'distribucion_titulo', 'distribucion_descripcion', 'distribucion_url_descarga']].drop_duplicates()
            
            # Optimizar procesamiento de series con numba si está disponible
            st.info("⚡ Calculando estadísticas de series...")
            try:
                from numba import jit
                
                @jit(nopython=True)
                def calculate_stats_numba(serie_ids, valores):
                    """Función optimizada con numba para calcular estadísticas"""
                    unique_series = np.unique(serie_ids)
                    stats = []
                    
                    for serie_id in unique_series:
                        mask = serie_ids == serie_id
                        serie_values = valores[mask]
                        
                        if len(serie_values) > 0:
                            stats.append([
                                serie_id,
                                np.min(serie_values),
                                np.max(serie_values),
                                len(serie_values),
                                np.mean(serie_values),
                                np.std(serie_values)
                            ])
                    
                    return np.array(stats)
                
                # Usar numba para estadísticas
                serie_ids_array = valores_df['serie_id'].cat.codes.values
                valores_array = valores_df['valor'].values
                
                stats_array = calculate_stats_numba(serie_ids_array, valores_array)
                
                serie_info = pd.DataFrame(
                    stats_array,
                    columns=['serie_id_code', 'minimo', 'maximo', 'cantidad_valores', 'promedio', 'desv_std']
                )
                
                # Mapear códigos de vuelta a IDs
                serie_id_mapping = dict(enumerate(valores_df['serie_id'].cat.categories))
                serie_info['serie_id'] = serie_info['serie_id_code'].map(serie_id_mapping)
                serie_info = serie_info[['serie_id', 'minimo', 'maximo', 'cantidad_valores', 'promedio', 'desv_std']]
                
            except ImportError:
                # Fallback sin numba
                serie_info = valores_df.groupby('serie_id').agg({
                    'valor': ['min', 'max', 'count', 'mean', 'std']
                }).reset_index()
                
                serie_info.columns = ['serie_id', 'minimo', 'maximo', 'cantidad_valores', 'promedio', 'desv_std']
            
            # No incluir datos de consultas ya que no están disponibles en la API oficial
            consultas_df = pd.DataFrame()
            
            # Limpiar archivos temporales
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Optimizar uso de memoria
            def optimize_dataframe_memory(df):
                """Optimiza el uso de memoria de un DataFrame"""
                for col in df.columns:
                    if df[col].dtype == 'object':
                        if df[col].nunique() / len(df) < 0.5:
                            df[col] = df[col].astype('category')
                    elif df[col].dtype == 'float64':
                        if df[col].isna().sum() == 0:
                            df[col] = df[col].astype('float32')
                return df
            
            # Aplicar optimización de memoria a DataFrames grandes
            if len(valores_df) > 10000:
                valores_df = optimize_dataframe_memory(valores_df)
            
            return {
                'index': index_df,
                'metadatos': metadatos_df,
                'valores': valores_df,
                'serie': serie_info,
                'dataset': dataset_df,
                'distribucion': distribucion_df,
                'consultas': consultas_df,
                'fuentes': fuentes_df
            }
            
        except Exception as e:
            st.error(f"Error al descargar y procesar datos: {e}")
            return None

@st.cache_data(ttl=1800)  # Cache por 30 minutos
def obtener_series_disponibles(datos):
    """Obtiene las series disponibles con metadatos con optimización de velocidad"""
    if datos is None:
        return pd.DataFrame()
    
    # Optimizar merge usando índices
    metadatos_subset = datos['metadatos'][['serie_id', 'serie_titulo', 'serie_unidades', 'serie_descripcion']].copy()
    dataset_subset = datos['dataset'][['dataset_id', 'dataset_titulo', 'dataset_fuente', 'dataset_descriptivo']].copy()
    
    # Usar merge optimizado
    series_info = datos['index'].merge(
        metadatos_subset, 
        on='serie_id', 
        how='left'
    ).merge(
        dataset_subset, 
        on='dataset_id', 
        how='left'
    )
    
    return series_info

@st.cache_data(ttl=900)  # Cache por 15 minutos
def obtener_valores_serie(serie_id, datos):
    """Obtiene los valores históricos de una serie específica con optimización de velocidad"""
    if datos is None:
        return pd.DataFrame()
    
    # Optimizar filtrado usando índices
    valores_df = datos['valores']
    
    # Crear índice si no existe
    if not valores_df.index.is_monotonic_increasing:
        valores_df = valores_df.sort_index()
    
    # Filtrado optimizado
    valores_serie = valores_df[valores_df['serie_id'] == serie_id].copy()
    
    # Ordenar solo si es necesario
    if not valores_serie.empty and not valores_serie['indice_tiempo'].is_monotonic_increasing:
        valores_serie = valores_serie.sort_values('indice_tiempo')
    
    return valores_serie

def crear_grafico_serie(valores_df, titulo, unidades):
    """Crea un gráfico interactivo para una serie temporal con optimización de velocidad"""
    if valores_df.empty:
        return None
    
    # Optimizar datos para el gráfico
    if len(valores_df) > 1000:
        # Muestrear datos para series muy largas
        step = len(valores_df) // 1000
        valores_df = valores_df.iloc[::step].copy()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=valores_df['indice_tiempo'],
        y=valores_df['valor'],
        mode='lines+markers' if len(valores_df) < 100 else 'lines',
        name=titulo,
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4) if len(valores_df) < 100 else dict(size=2),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Valor:</b> %{y:,.2f}<br><extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{titulo} ({unidades})",
        xaxis_title="Fecha",
        yaxis_title=f"Valor ({unidades})",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        # Optimizaciones de rendimiento
        uirevision=True,
        dragmode=False
    )
    
    return fig

def crear_grafico_comparativo(series_data, titulo):
    """Crea un gráfico comparativo de múltiples series"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, (serie_id, data) in enumerate(series_data.items()):
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['indice_tiempo'],
                y=data['valor'],
                mode='lines',
                name=serie_id,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x}<br>Valor: %{y:,.2f}<extra></extra>'
            ))
    
    fig.update_layout(
        title=titulo,
        xaxis_title="Fecha",
        yaxis_title="Valor",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

def mostrar_estadisticas_generales(datos):
    """Muestra estadísticas generales del dataset"""
    if datos is None:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Series", len(datos['index']))
    
    with col2:
        st.metric("Categorías", datos['index']['catalogo_id'].nunique())
    
    with col3:
        st.metric("Total de Valores", len(datos['valores']))
    
    with col4:
        st.metric("Fuentes de Datos", datos['dataset']['dataset_fuente'].nunique())

def main():
    # Inicializar session_state para persistencia
    if 'datos_cargados' not in st.session_state:
        st.session_state.datos_cargados = None
    if 'series_info' not in st.session_state:
        st.session_state.series_info = None
    if 'categoria_seleccionada' not in st.session_state:
        st.session_state.categoria_seleccionada = 'Todas'
    if 'frecuencia_seleccionada' not in st.session_state:
        st.session_state.frecuencia_seleccionada = 'Todas'
    if 'busqueda_texto' not in st.session_state:
        st.session_state.busqueda_texto = ''
    if 'serie_seleccionada' not in st.session_state:
        st.session_state.serie_seleccionada = None
    if 'categoria_analisis' not in st.session_state:
        st.session_state.categoria_analisis = None
    if 'series_comparar' not in st.session_state:
        st.session_state.series_comparar = []
    if 'tab_actual' not in st.session_state:
        st.session_state.tab_actual = "🏠 Dashboard General"
    
    # Título principal
    st.title("📊 Datos Económicos de Argentina")
    st.markdown("### Ministerio de Economía de la Nación - Series de Tiempo")
    st.markdown("---")
    
    # Información sobre datos reales y optimizaciones
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("✅ **Todos los datos mostrados son REALES y provienen directamente de las APIs oficiales del Ministerio de Economía de la Nación Argentina.**")
    
    with col2:
        st.success("⚡ **Optimizada para velocidad máxima**")
    
    # Botón para recargar datos
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if st.button("🔄 Recargar Datos", key="reload_button"):
            st.session_state.datos_cargados = None
            st.session_state.series_info = None
            st.rerun()
    
    # Información sobre mapeos descriptivos
    with st.expander("ℹ️ Información sobre los datos mostrados"):
        st.info("""
        **Nombres Descriptivos Implementados:**
        
        **Frecuencias de Actualización:**
        - R/P1Y → Anual
        - R/P6M → Semestral  
        - R/P3M → Trimestral
        - R/P1M → Mensual
        - R/P1D → Diaria
        
        **Fuentes de Datos:**
        - sspm → Sistema de Cuentas Nacionales
        - snic → Sistema Nacional de Información de Comercio
        - bcra → Banco Central de la República Argentina
        - agroindustria → Ministerio de Agroindustria
        - turismo → Turismo
        - obras → Obras Públicas
        - Y muchos más...
        """)
    
    # Descargar y procesar datos con persistencia
    if st.session_state.datos_cargados is None:
        datos = descargar_y_procesar_datos()
        if datos is not None:
            st.session_state.datos_cargados = datos
        else:
            st.error("No se pudieron cargar los datos. Verifica tu conexión a internet.")
            return
    else:
        datos = st.session_state.datos_cargados
        st.success("✅ Datos cargados desde cache - Sin recarga necesaria")
    
    # Sidebar para navegación
    st.sidebar.title("🎯 Navegación")
    
    # Indicador de estado de persistencia
    if st.session_state.datos_cargados is not None:
        st.sidebar.success("✅ Datos persistentes")
        st.sidebar.info(f"📊 {len(st.session_state.datos_cargados['valores']):,} valores cargados")
    else:
        st.sidebar.warning("⏳ Cargando datos...")
    
    st.sidebar.markdown("---")
    
    # Botones de control
    if st.sidebar.button("🗑️ Limpiar Selecciones", key="clear_selections"):
        st.session_state.categoria_seleccionada = 'Todas'
        st.session_state.frecuencia_seleccionada = 'Todas'
        st.session_state.busqueda_texto = ''
        st.session_state.serie_seleccionada = None
        st.session_state.categoria_analisis = None
        st.session_state.series_comparar = []
        st.rerun()
    
    if st.sidebar.button("🔄 Limpiar Cache", key="clear_cache"):
        st.session_state.datos_cargados = None
        st.session_state.series_info = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Estadísticas generales
    st.header("📈 Estadísticas Generales")
    mostrar_estadisticas_generales(datos)
    st.markdown("---")
    
    # Obtener series disponibles con persistencia
    if st.session_state.series_info is None:
        series_info = obtener_series_disponibles(datos)
        st.session_state.series_info = series_info
    else:
        series_info = st.session_state.series_info
    
    # Pestañas principales con persistencia
    tabs = st.tabs([
        "🏠 Dashboard General", 
        "📊 Explorador de Series", 
        "🔍 Análisis por Categoría",
        "📈 Comparación de Series",
        "📋 Metadatos y Fuentes"
    ])
    
    # Actualizar tab actual basado en la selección
    tab_names = ["🏠 Dashboard General", "📊 Explorador de Series", "🔍 Análisis por Categoría", "📈 Comparación de Series", "📋 Metadatos y Fuentes"]
    for i, tab in enumerate(tabs):
        if tab:
            st.session_state.tab_actual = tab_names[i]
            break
    
    with tabs[0]:
        st.header("🏠 Dashboard General")
        
        # Resumen por categoría
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Series por Categoría")
            categoria_counts = datos['index']['catalogo_id'].value_counts()
            fig_cat = px.pie(
                values=categoria_counts.values, 
                names=categoria_counts.index,
                title="Distribución de Series por Categoría"
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.subheader("📅 Frecuencia de Actualización")
            freq_counts = datos['index']['frecuencia_descriptiva'].value_counts()
            fig_freq = px.bar(
                x=freq_counts.index, 
                y=freq_counts.values,
                title="Frecuencia de Actualización de Series",
                labels={'x': 'Frecuencia', 'y': 'Cantidad de Series'}
            )
            st.plotly_chart(fig_freq, use_container_width=True)
        
        # Información adicional sobre las series
        st.subheader("📊 Resumen de Series Disponibles")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Series por Frecuencia:**")
            freq_summary = datos['index']['frecuencia_descriptiva'].value_counts()
            st.dataframe(freq_summary.to_frame('Cantidad'))
        
        with col2:
            st.write("**Series por Categoría:**")
            cat_summary = datos['index']['catalogo_id'].value_counts()
            st.dataframe(cat_summary.to_frame('Cantidad'))
    
    with tabs[1]:
        st.header("📊 Explorador de Series")
        
        # Filtros con persistencia
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categorias = ['Todas'] + list(series_info['catalogo_id'].unique())
            categoria_seleccionada = st.selectbox(
                "Categoría:", 
                categorias,
                index=categorias.index(st.session_state.categoria_seleccionada) if st.session_state.categoria_seleccionada in categorias else 0,
                key="categoria_selector"
            )
            st.session_state.categoria_seleccionada = categoria_seleccionada
        
        with col2:
            frecuencias = ['Todas'] + list(series_info['frecuencia_descriptiva'].unique())
            frecuencia_seleccionada = st.selectbox(
                "Frecuencia:", 
                frecuencias,
                index=frecuencias.index(st.session_state.frecuencia_seleccionada) if st.session_state.frecuencia_seleccionada in frecuencias else 0,
                key="frecuencia_selector"
            )
            st.session_state.frecuencia_seleccionada = frecuencia_seleccionada
        
        with col3:
            busqueda = st.text_input(
                "Buscar por título:", 
                value=st.session_state.busqueda_texto,
                key="busqueda_input"
            )
            st.session_state.busqueda_texto = busqueda
        
        # Filtrar series
        series_filtradas = series_info.copy()
        
        if categoria_seleccionada != 'Todas':
            series_filtradas = series_filtradas[series_filtradas['catalogo_id'] == categoria_seleccionada]
        
        if frecuencia_seleccionada != 'Todas':
            series_filtradas = series_filtradas[series_filtradas['frecuencia_descriptiva'] == frecuencia_seleccionada]
        
        if busqueda:
            series_filtradas = series_filtradas[
                series_filtradas['serie_titulo'].str.contains(busqueda, case=False, na=False)
            ]
        
        # Mostrar series filtradas
        st.subheader(f"📋 Series Encontradas: {len(series_filtradas)}")
        
        if len(series_filtradas) > 0:
            # Selector de serie con persistencia
            serie_options = series_filtradas['serie_id'].tolist()
            serie_format_func = lambda x: f"{x} - {series_filtradas[series_filtradas['serie_id']==x]['serie_titulo'].iloc[0]}"
            
            # Determinar índice inicial
            initial_index = 0
            if st.session_state.serie_seleccionada in serie_options:
                initial_index = serie_options.index(st.session_state.serie_seleccionada)
            
            serie_seleccionada = st.selectbox(
                "Selecciona una serie para visualizar:",
                options=serie_options,
                index=initial_index,
                format_func=serie_format_func,
                key="serie_selector"
            )
            st.session_state.serie_seleccionada = serie_seleccionada
            
            if serie_seleccionada:
                # Obtener información de la serie
                info_serie = series_filtradas[series_filtradas['serie_id'] == serie_seleccionada].iloc[0]
                
                # Obtener valores de la serie
                valores_serie = obtener_valores_serie(serie_seleccionada, datos)
                
                if not valores_serie.empty:
                    # Información de la serie
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Título", info_serie['serie_titulo'])
                        st.metric("Unidades", info_serie['serie_unidades'])
                    
                    with col2:
                        st.metric("Categoría", info_serie['catalogo_id'])
                        st.metric("Frecuencia", info_serie['frecuencia_descriptiva'])
                    
                    with col3:
                        st.metric("Total de Valores", len(valores_serie))
                        st.metric("Período", f"{valores_serie['indice_tiempo'].min().strftime('%Y-%m')} a {valores_serie['indice_tiempo'].max().strftime('%Y-%m')}")
                    
                    # Gráfico de la serie
                    st.subheader("📈 Evolución Temporal")
                    fig = crear_grafico_serie(valores_serie, info_serie['serie_titulo'], info_serie['serie_unidades'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Estadísticas descriptivas
                    st.subheader("📊 Estadísticas Descriptivas")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Resumen Estadístico:**")
                        stats = valores_serie['valor'].describe()
                        st.dataframe(stats.to_frame().T)
                    
                    with col2:
                        st.write("**Últimos 10 Valores:**")
                        st.dataframe(valores_serie.tail(10)[['indice_tiempo', 'valor']])
                
                else:
                    st.warning("No se encontraron valores para esta serie.")
        else:
            st.info("No se encontraron series con los filtros aplicados.")
    
    with tabs[2]:
        st.header("🔍 Análisis por Categoría")
        
        # Selector de categoría con persistencia
        categorias_disponibles = datos['index']['catalogo_id'].unique()
        
        # Determinar índice inicial
        initial_index = 0
        if st.session_state.categoria_analisis in categorias_disponibles:
            initial_index = list(categorias_disponibles).index(st.session_state.categoria_analisis)
        
        categoria_analisis = st.selectbox(
            "Selecciona una categoría para analizar:",
            options=categorias_disponibles,
            index=initial_index,
            key="categoria_analisis_selector"
        )
        st.session_state.categoria_analisis = categoria_analisis
        
        if categoria_analisis:
            # Obtener series de la categoría
            series_categoria = series_info[series_info['catalogo_id'] == categoria_analisis]
            
            st.subheader(f"📊 Análisis de {categoria_analisis.upper()}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Series", len(series_categoria))
                st.metric("Fuentes de Datos", series_categoria['dataset_fuente'].nunique())
            
            with col2:
                st.metric("Frecuencias", series_categoria['frecuencia_descriptiva'].nunique())
                st.metric("Datasets", series_categoria['dataset_descriptivo'].nunique())
            
            # Gráfico de frecuencias
            st.subheader("📅 Distribución por Frecuencia")
            freq_cat = series_categoria['frecuencia_descriptiva'].value_counts()
            fig_freq_cat = px.pie(
                values=freq_cat.values, 
                names=freq_cat.index,
                title=f"Frecuencias en {categoria_analisis}"
            )
            st.plotly_chart(fig_freq_cat, use_container_width=True)
            
            # Lista de series de la categoría
            st.subheader("📋 Series Disponibles")
            st.dataframe(
                series_categoria[['serie_id', 'serie_titulo', 'frecuencia_descriptiva', 'dataset_descriptivo']],
                use_container_width=True
            )
    
    with tabs[3]:
        st.header("📈 Comparación de Series")
        
        # Filtro de búsqueda para facilitar selección
        st.info("💡 **Consejo**: Usa el campo de búsqueda para filtrar las series y facilitar la selección")
        
        busqueda_comparacion = st.text_input(
            "🔍 Buscar series para comparar:",
            placeholder="Escribe parte del título de la serie...",
            key="busqueda_comparacion"
        )
        
        # Selector múltiple de series con persistencia
        # Crear opciones con títulos descriptivos
        series_options = []
        series_id_to_title = {}
        
        for _, row in series_info.iterrows():
            serie_id = row['serie_id']
            serie_titulo = row['serie_titulo']
            categoria = row['catalogo_id']
            frecuencia = row['frecuencia_descriptiva']
            
            # Aplicar filtro de búsqueda
            if busqueda_comparacion:
                if busqueda_comparacion.lower() not in serie_titulo.lower() and busqueda_comparacion.lower() not in categoria.lower():
                    continue
            
            # Crear opción descriptiva
            option_text = f"{serie_titulo} ({categoria} - {frecuencia})"
            series_options.append(option_text)
            series_id_to_title[option_text] = serie_id
        
        # Convertir IDs guardados a opciones descriptivas
        default_options = []
        for serie_id in st.session_state.series_comparar:
            if serie_id in series_info['serie_id'].values:
                info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                option_text = f"{info['serie_titulo']} ({info['catalogo_id']} - {info['frecuencia_descriptiva']})"
                default_options.append(option_text)
        
        # Mostrar contador de opciones
        st.info(f"📊 {len(series_options)} series disponibles para selección")
        
        series_comparar_options = st.multiselect(
            "Selecciona series para comparar (máximo 5):",
            options=series_options,
            default=default_options,
            max_selections=5,
            key="series_comparar_selector"
        )
        
        # Convertir opciones seleccionadas de vuelta a IDs
        series_comparar = [series_id_to_title[option] for option in series_comparar_options]
        st.session_state.series_comparar = series_comparar
        
        # Mostrar información sobre las series seleccionadas
        if series_comparar:
            st.subheader("📋 Series Seleccionadas para Comparación")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                for i, serie_id in enumerate(series_comparar, 1):
                    if serie_id in series_info['serie_id'].values:
                        info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                        st.write(f"**{i}.** {info['serie_titulo']} ({info['catalogo_id']} - {info['frecuencia_descriptiva']})")
            
            with col2:
                st.metric("Series Seleccionadas", len(series_comparar))
            
            with col3:
                if st.button("🗑️ Limpiar Selección", key="limpiar_comparacion"):
                    st.session_state.series_comparar = []
                    st.rerun()
        
        if len(series_comparar) >= 2:
            # Obtener datos de las series seleccionadas
            series_data = {}
            for serie_id in series_comparar:
                valores = obtener_valores_serie(serie_id, datos)
                if not valores.empty:
                    series_data[serie_id] = valores
            
            if len(series_data) >= 2:
                # Gráfico comparativo
                st.subheader("📊 Comparación de Series")
                fig_comp = crear_grafico_comparativo(series_data, "Comparación de Series Seleccionadas")
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # Tabla comparativa
                st.subheader("📋 Resumen Comparativo")
                
                resumen_data = []
                for serie_id, valores in series_data.items():
                    info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                    resumen_data.append({
                        'Serie ID': serie_id,
                        'Título': info['serie_titulo'],
                        'Categoría': info['catalogo_id'],
                        'Unidades': info['serie_unidades'],
                        'Valores': len(valores),
                        'Inicio': valores['indice_tiempo'].min().strftime('%Y-%m'),
                        'Fin': valores['indice_tiempo'].max().strftime('%Y-%m'),
                        'Promedio': valores['valor'].mean(),
                        'Máximo': valores['valor'].max(),
                        'Mínimo': valores['valor'].min()
                    })
                
                resumen_df = pd.DataFrame(resumen_data)
                st.dataframe(resumen_df, use_container_width=True)
            else:
                st.warning("Se necesitan al menos 2 series con datos válidos para la comparación.")
        else:
            st.info("Selecciona al menos 2 series para comparar.")
    
    with tabs[4]:
        st.header("📋 Metadatos y Fuentes")
        
        # Información de datasets
        st.subheader("📊 Datasets Disponibles")
        st.dataframe(
            datos['dataset'][['dataset_id', 'dataset_titulo', 'dataset_descriptivo', 'dataset_fuente', 'dataset_responsable']],
            use_container_width=True
        )
        
        # Información de fuentes
        st.subheader("🔗 Fuentes de Datos")
        if not datos['fuentes'].empty:
            st.dataframe(datos['fuentes'], use_container_width=True)
        else:
            st.info("No hay información de fuentes disponible.")
        
        # Información adicional sobre los datos
        st.subheader("📈 Información Adicional")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Resumen de Datasets:**")
            dataset_summary = datos['dataset']['dataset_fuente'].value_counts()
            st.dataframe(dataset_summary.to_frame('Cantidad de Series'))
        
        with col2:
            st.write("**Responsables de Datasets:**")
            responsables_summary = datos['dataset']['dataset_responsable'].value_counts().head(10)
            st.dataframe(responsables_summary.to_frame('Cantidad de Datasets'))
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>📊 Datos proporcionados por el Ministerio de Economía de la Nación Argentina</p>
        <p>Desarrollado con Streamlit | Fuente: <a href='https://apis.datos.gob.ar/series/api/'>API de Datos Abiertos</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 
