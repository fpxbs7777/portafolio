import requests
import pandas as pd
import numpy as np
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import streamlit as st
import plotly.graph_objects as go

class Inversor:
    """Clase para manejar la conexión con la API de Invertir Online y optimización de cartera."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.bearer_token = None
        self.refresh_token = None
        self.perfil_inversor = None
        self.activos_disponibles = {}
        
    def obtener_tokens(self) -> bool:
        """Obtiene tokens de acceso usando las credenciales."""
        url = 'https://api.invertironline.com/token'
        data = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            response = requests.post(url, data=data, headers=headers)
            if response.status_code == 200:
                tokens = response.json()
                self.bearer_token = tokens['access_token']
                self.refresh_token = tokens['refresh_token']
                return True
            else:
                print(f'Error al obtener tokens: {response.status_code}')
                print(response.text)
                return False
        except Exception as e:
            print(f'Error de conexión: {str(e)}')
            return False

# --- Asset Detection and Portfolio Optimization Functions ---
def detectar_tipo_activo_iol(simbolo, bearer_token):
    url = f"https://api.invertironline.com/api/v2/buscar?query={simbolo}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'titulos' in data:
                for titulo in data['titulos']:
                    if titulo.get('simbolo') == simbolo:
                        tipo = titulo.get('tipoInstrumento', '').lower()
                        if 'accion' in tipo:
                            return 'accion'
                        elif 'bono' in tipo or 'obligacion' in tipo:
                            return 'bono'
                        elif 'cedear' in tipo:
                            return 'cedear'
                        elif 'fondo' in tipo or 'fci' in tipo:
                            return 'fci'
                        elif 'opcion' in tipo:
                            return 'opcion'
            return 'otro'
        return 'otro'
    except Exception:
        return 'otro'

def optimizar_pesos_por_perfil(activos, perfil='moderado'):
    perfiles = {
        'conservador': {'bono': 0.7, 'accion': 0.2, 'cedear': 0.05, 'fci': 0.05, 'otro': 0.0},
        'moderado': {'bono': 0.5, 'accion': 0.3, 'cedear': 0.15, 'fci': 0.05, 'otro': 0.0},
        'agresivo': {'bono': 0.2, 'accion': 0.6, 'cedear': 0.15, 'fci': 0.05, 'otro': 0.0}
    }
    if perfil not in perfiles:
        perfil = 'moderado'
    activos_por_tipo = {'bono': [], 'accion': [], 'cedear': [], 'fci': [], 'otro': []}
    for activo in activos:
        tipo = activo.get('tipo_detectado', 'otro')
        activos_por_tipo[tipo].append(activo)
    pesos_perfil = perfiles[perfil]
    portafolio_optimizado = []
    for tipo, activos_tipo in activos_por_tipo.items():
        if not activos_tipo:
            continue
        peso_total = pesos_perfil[tipo]
        peso_individual = peso_total / len(activos_tipo)
        for activo in activos_tipo:
            activo['peso_optimizado'] = peso_individual
            portafolio_optimizado.append(activo)
    return portafolio_optimizado

# --- Main Streamlit App ---
def main():
    st.title("IOL Portfolio Analyzer")
    
    # Authentication
    bearer_token = st.session_state.get('bearer_token')
    if not bearer_token:
        usuario = st.text_input("Usuario IOL")
        contraseña = st.text_input("Contraseña", type="password")
        if st.button("Iniciar sesión"):
            bearer_token, refresh_token = obtener_tokens(usuario, contraseña)
            if bearer_token:
                st.session_state.bearer_token = bearer_token
                st.session_state.refresh_token = refresh_token
                st.success("Autenticación exitosa")
            else:
                st.error("Error en autenticación")
        return
    
    # Client selection
    clientes = obtener_lista_clientes(bearer_token)
    if not clientes:
        st.warning("No se encontraron clientes")
        return
    
    cliente_seleccionado = st.selectbox("Seleccionar cliente", [c['nombre'] for c in clientes])
    id_cliente = next(c['id'] for c in clientes if c['nombre'] == cliente_seleccionado)
    
    # Get portfolio
    portafolio = obtener_portafolio(bearer_token, id_cliente)
    if not portafolio:
        st.warning("No se encontró portafolio")
        return
    
    # Add asset type detection
    st.subheader("Detección de tipos de activo")
    activos_con_tipo = []
    for activo in portafolio.get('activos', []):
        simbolo = activo.get('simbolo')
        if simbolo:
            tipo = detectar_tipo_activo_iol(simbolo, bearer_token)
            activo['tipo_detectado'] = tipo
            activos_con_tipo.append(activo)
    
    # Portfolio optimization by profile
    st.subheader("Optimización de Portafolio")
    perfil = st.selectbox("Perfil de inversión", ["conservador", "moderado", "agresivo"])
    
    if st.button("Optimizar Portafolio"):
        portafolio_optimizado = optimizar_pesos_por_perfil(activos_con_tipo, perfil)
        
        # Display optimized portfolio
        st.write("## Portafolio Optimizado")
        df = pd.DataFrame([
            {
                'Símbolo': a['simbolo'],
                'Tipo': a['tipo_detectado'],
                'Peso': f"{a['peso_optimizado']*100:.1f}%"
            } for a in portafolio_optimizado
        ])
        st.dataframe(df)
        
        # Pie chart of allocation
        fig = go.Figure(data=[go.Pie(
            labels=df['Símbolo'],
            values=[float(p[:-1]) for p in df['Peso']],
            hoverinfo='label+percent',
            textinfo='value'
        )])
        st.plotly_chart(fig)
    
    # Existing portfolio analysis
    # ... [resto del código existente] ...

def obtener_tokens(usuario, contraseña):
    # Implementación de obtener_tokens
    pass

def obtener_lista_clientes(bearer_token):
    # Implementación de obtener_lista_clientes
    pass

def obtener_portafolio(bearer_token, id_cliente):
    # Implementación de obtener_portafolio
    pass

if __name__ == "__main__":
    main()
