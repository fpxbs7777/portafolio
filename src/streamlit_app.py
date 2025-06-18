import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats # Added for skewness, kurtosis, jarque_bera
import random
import warnings
import streamlit.components.v1 as components
import os

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide"
)

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
        error_msg = f'Error HTTP al obtener tokens: {http_err}'
        if hasattr(http_err, 'response') and http_err.response:
            status = http_err.response.status_code
            if status == 400:
                error_msg += "\nVerifique sus credenciales (usuario/contraseña). El servidor indicó 'Bad Request'."
            elif status == 401:
                error_msg += "\nNo autorizado. Verifique sus credenciales o permisos."
        st.error(error_msg)
        return None, None
    except Exception as e:
        st.error(f'Error de conexión: {str(e)}')
        return None, None

def main():
    """
    Función principal de la aplicación Streamlit
    """
    st.title("📊 IOL Portfolio Analyzer")
    st.markdown("### Analizador Avanzado de Portafolios IOL")
    
    # Initialize all session state variables
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
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = None
    if 'estado_cuenta' not in st.session_state:
        st.session_state.estado_cuenta = None
    if 'test_data' not in st.session_state:
        st.session_state.test_data = None
    if 'test_result' not in st.session_state:
        st.session_state.test_result = None
    
    # Sidebar for authentication
    with st.sidebar:
        st.header("🔐 Autenticación IOL")
        
        if st.session_state.token_acceso is None:
            with st.form("login_form"):
                usuario = st.text_input("Usuario")
                contraseña = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar"):
                    with st.spinner("Autenticando..."):
                        token, refresh_token = obtener_tokens(usuario, contraseña)
                        if token:
                            st.session_state.token_acceso = token
                            st.session_state.refresh_token = refresh_token
                            st.session_state.clientes = obtener_lista_clientes(token)
                            st.success("Autenticación exitosa!")
                        else:
                            st.error("Error en autenticación")
        else:
            st.success("✅ Autenticado")
            if st.button("Cerrar sesión"):
                st.session_state.clear()
                st.rerun()
            
            # Client selection
            if st.session_state.clientes:
                cliente_options = {c['nombre']: c['id'] for c in st.session_state.clientes}
                selected_name = st.selectbox("Seleccionar cliente", options=list(cliente_options.keys()))
                st.session_state.cliente_seleccionado = cliente_options[selected_name]
            
            # Date range selection
            st.header("📅 Rango de fechas")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.fecha_desde = st.date_input("Desde", value=st.session_state.fecha_desde)
            with col2:
                st.session_state.fecha_hasta = st.date_input("Hasta", value=st.session_state.fecha_hasta)
    
    # Main content
    if st.session_state.token_acceso:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Portafolio", "💵 Estado de Cuenta", "📈 Mercado", "🧪 Test Inversor"])
        
        # ... (existing tabs implementation)
        
        with tab4:
            st.header("🧪 Test de Perfil de Inversor")
            
            if st.session_state.cliente_seleccionado:
                if st.button("Obtener Test"):
                    with st.spinner("Cargando preguntas..."):
                        st.session_state.test_data = obtener_test_inversor(st.session_state.token_acceso)
                
                if st.session_state.test_data:
                    with st.form("test_form"):
                        st.subheader("Instrumentos invertidos anteriormente")
                        instrumentos = [i['nombre'] for i in st.session_state.test_data['instrumentosInvertidosAnteriormente']['instrumentos']]
                        instrumentos_seleccionados = st.multiselect(
                            st.session_state.test_data['instrumentosInvertidosAnteriormente']['pregunta'],
                            instrumentos
                        )
                        
                        st.subheader("Nivel de conocimiento")
                        niveles = st.session_state.test_data['nivelesConocimientoInstrumentos']['niveles']
                        nivel_seleccionado = st.radio(
                            st.session_state.test_data['nivelesConocimientoInstrumentos']['pregunta'],
                            [n['nombre'] for n in niveles]
                        )
                        
                        # Add similar form fields for other questions...
                        
                        if st.form_submit_button("Enviar Test"):
                            respuestas = {
                                "enviarEmailCliente": True,
                                "instrumentosInvertidosAnteriormente": [
                                    i['id'] for i in st.session_state.test_data['instrumentosInvertidosAnteriormente']['instrumentos'] 
                                    if i['nombre'] in instrumentos_seleccionados
                                ],
                                "nivelesConocimientoInstrumentos": [
                                    n['id'] for n in niveles 
                                    if n['nombre'] == nivel_seleccionado
                                ],
                                # Add other answer fields...
                            }
                            
                            with st.spinner("Analizando perfil..."):
                                st.session_state.test_result = enviar_test_inversor(
                                    st.session_state.token_acceso,
                                    respuestas,
                                    st.session_state.cliente_seleccionado
                                )
                
                if st.session_state.test_result:
                    st.success("✅ Test completado")
                    perfil = st.session_state.test_result['perfilSugerido']
                    st.subheader(f"Perfil sugerido: {perfil['nombre']}")
                    st.write(perfil['detalle'])
                    
                    st.subheader("Composición recomendada:")
                    for comp in perfil['perfilComposiciones']:
                        st.write(f"- {comp['nombre']}: {comp['porcentaje']}%")
            else:
                st.warning("Seleccione un cliente en el sidebar")
    
    # ... (rest of existing main function)

if __name__ == "__main__":
    main()
