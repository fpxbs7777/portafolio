import os
os.environ["STREAMLIT_HOME"] = "/tmp"
os.environ["STREAMLIT_RUNTIME_HOME"] = "/tmp"
os.environ["STREAMLIT_STATIC_HOME"] = "/tmp"
os.environ["STREAMLIT_CONFIG_DIR"] = "/tmp"
os.environ["XDG_CONFIG_HOME"] = "/tmp"
os.environ["HOME"] = "/tmp"

import streamlit as st
import requests

# Configuración de la página
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal de la aplicación"""
    st.title("📊 IOL Portfolio Analyzer")
    st.write("Bienvenido al analizador de portafolios")

if __name__ == "__main__":
    main()
