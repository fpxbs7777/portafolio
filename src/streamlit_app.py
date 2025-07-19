import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Indicadores Económicos de Argentina",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 30px;}
    .section-header {font-size: 1.8rem; color: #2c3e50; margin: 20px 0 15px 0;}
    .metric-card {background-color: #f8f9fa; border-radius: 10px; padding: 15px; margin: 10px 0;}
    .metric-value {font-size: 1.5rem; font-weight: bold; color: #1f77b4;}
    .metric-label {font-size: 1rem; color: #6c757d;}
</style>
""", unsafe_allow_html=True)

# App title
st.markdown('<h1 class="main-header">Indicadores Económicos de Argentina</h1>', unsafe_allow_html=True)

# Data sources
DATA_SOURCES = {
    "Actividad Económica": {
        "PIB": "https://www.economia.gob.ar/download/infoeco/actividad_ied.xlsx",
        "EMAE": "https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_mensual.xls"
    },
    "Precios": {
        "Inflación Mensual (IPC)": "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_2016_10_nivel_general.xls",
        "Inflación Interanual (IPC)": "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_2016_10_variaciones.xls"
    },
    "Mercado Laboral": {
        "Tasa de Desempleo": "https://www.indec.gob.ar/ftp/cuadros/sociedad/eph_continua_tasa_desocupacion.xls"
    },
    "Sector Externo": {
        "Tipo de Cambio": "https://www.bcra.gob.ar/PublicacionesEstadisticas/Tipo_de_cambio_minorista_1.xls"
    }
}

def load_data(url):
    """Load data from Excel/CSV URL"""
    try:
        response = requests.get(url)
        if url.endswith('.xls') or url.endswith('.xlsx'):
            return pd.read_excel(BytesIO(response.content))
        else:
            return pd.read_csv(BytesIO(response.content))
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return None

def display_metric_card(title, value, delta=None):
    """Display a metric card with optional delta indicator"""
    st.metric(label=title, value=value, delta=delta)

def main():
    # Sidebar for navigation
    st.sidebar.title("Navegación")
    category = st.sidebar.selectbox("Categoría", list(DATA_SOURCES.keys()))
    
    st.markdown(f'<h2 class="section-header">{category}</h2>', unsafe_allow_html=True)
    
    # Display available indicators for the selected category
    indicators = DATA_SOURCES[category]
    selected_indicator = st.selectbox("Seleccione un indicador", list(indicators.keys()))
    
    # Load and display data
    data_url = indicators[selected_indicator]
    st.info(f"Fuente: {data_url}")
    
    data = load_data(data_url)
    
    if data is not None:
        # Display raw data
        st.subheader("Datos")
        st.dataframe(data.head())
        
        # Display basic statistics
        st.subheader("Estadísticas Básicas")
        st.write(data.describe())
        
        # Create interactive plot
        st.subheader("Visualización")
        
        # Simple visualization - adjust based on actual data structure
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) > 0:
            x_axis = st.selectbox("Eje X", data.columns, index=0)
            y_axis = st.selectbox("Eje Y", numeric_cols, index=0)
            
            if st.checkbox("Mostrar gráfico de líneas"):
                fig = px.line(data, x=x_axis, y=y_axis, title=f"{selected_indicator} a lo largo del tiempo")
                st.plotly_chart(fig, use_container_width=True)
                
            if st.checkbox("Mostrar histograma"):
                fig = px.histogram(data, x=y_axis, title=f"Distribución de {selected_indicator}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron columnas numéricas para graficar.")
        
        # Download button for the data
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar datos como CSV",
            data=csv,
            file_name=f"{selected_indicator.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )
    else:
        st.error("No se pudieron cargar los datos. Por favor, intente más tarde.")

if __name__ == "__main__":
    main()
