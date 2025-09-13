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

def autenticar_usuario(usuario, contraseña):
    """Autentica el usuario con IOL y obtiene el token de acceso"""
    url = 'https://api.invertironline.com/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': usuario,
        'password': contraseña,
        'grant_type': 'password'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            st.error(f"Error de autenticación: {response.status_code}")
            if response.status_code == 401:
                st.error("Credenciales incorrectas. Verifica tu usuario y contraseña.")
            return None
    except Exception as e:
        st.error(f"Error al autenticar: {str(e)}")
        return None

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

def obtener_portafolio_argentina(token_portador):
    """Obtiene el portafolio de Argentina"""
    url = 'https://api.invertironline.com/api/v2/portafolio/argentina'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 500:
            st.warning("⚠️ No se pudo obtener el portafolio de Argentina")
            return None
        else:
            st.error(f"Error al obtener portafolio Argentina: {response.status_code}")
            if response.status_code == 401:
                st.error("Token de acceso inválido o expirado")
            elif response.status_code == 403:
                st.error("No tienes permisos para acceder al portafolio de Argentina")
        return None
    except Exception as e:
        st.error(f"Error al obtener portafolio Argentina: {str(e)}")
        return None

def obtener_portafolio_eeuu(token_portador):
    """Obtiene el portafolio de Estados Unidos"""
    url = 'https://api.invertironline.com/api/v2/portafolio/estados_Unidos'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 500:
            st.warning("⚠️ No se pudo obtener el portafolio de Estados Unidos")
            return None
        else:
            st.error(f"Error al obtener portafolio EEUU: {response.status_code}")
            if response.status_code == 401:
                st.error("Token de acceso inválido o expirado")
            elif response.status_code == 403:
                st.error("No tienes permisos para acceder al portafolio de Estados Unidos")
        return None
    except Exception as e:
        st.error(f"Error al obtener portafolio EEUU: {str(e)}")
        return None

def obtener_estado_cuenta(token_portador):
    """Obtiene el estado de cuenta general"""
    url = 'https://api.invertironline.com/api/v2/estadocuenta'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 500:
            st.warning("⚠️ No se pudo obtener el estado de cuenta")
            return None
        else:
            st.error(f"Error al obtener estado de cuenta: {response.status_code}")
            if response.status_code == 401:
                st.error("Token de acceso inválido o expirado")
            elif response.status_code == 403:
                st.error("No tienes permisos para acceder al estado de cuenta")
            return None
    except Exception as e:
        st.error(f"Error al obtener estado de cuenta: {str(e)}")
        return None
                
def filtrar_estado_cuenta_por_moneda(estado_cuenta, moneda="peso_Argentino"):
    """Filtra el estado de cuenta por moneda"""
    if not estado_cuenta or 'cuentas' not in estado_cuenta:
        return None
            
    cuentas_filtradas = [cuenta for cuenta in estado_cuenta['cuentas'] if cuenta.get('moneda') == moneda]
    
    if cuentas_filtradas:
        return {
            'cuentas': cuentas_filtradas,
            'estadisticas': estado_cuenta.get('estadisticas', []),
            'totalEnPesos': estado_cuenta.get('totalEnPesos', 0)
        }
    return None

def obtener_movimientos(token_portador, fecha_desde=None, fecha_hasta=None, pais="argentina"):
    """
    Obtiene los movimientos/operaciones de la cuenta usando la API de InvertirOnline
    
    Args:
        token_portador (str): Token de acceso para la autenticación
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
        pais (str): País para filtrar operaciones (argentina/estados_Unidos)
        
    Returns:
        list: Lista de operaciones/movimientos de la cuenta
    """
    url = 'https://api.invertironline.com/api/v2/operaciones'
    
    headers = obtener_encabezado_autorizacion(token_portador)
    
    # Parámetros de consulta para filtrar por fechas
    params = {
        'filtro.pais': pais
    }
    if fecha_desde:
        params['filtro.fechaDesde'] = fecha_desde
    if fecha_hasta:
        params['filtro.fechaHasta'] = fecha_hasta
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            operaciones = response.json()
            return operaciones
        else:
            st.error(f"Error al obtener movimientos: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Error al obtener movimientos: {str(e)}")
        return []

def obtener_notificaciones(token_portador):
    """Obtiene las notificaciones del asesor"""
    url = 'https://api.invertironline.com/api/v2/Notificacion'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            notificaciones = response.json()
            return notificaciones if isinstance(notificaciones, list) else [notificaciones]
        elif response.status_code == 500:
            st.warning("⚠️ No se pudieron obtener las notificaciones")
            return []
        else:
            st.error(f"Error al obtener notificaciones: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener notificaciones: {str(e)}")
        return []

def obtener_datos_perfil_asesor(token_portador):
    """Obtiene los datos del perfil del asesor"""
    url = 'https://api.invertironline.com/api/v2/datos-perfil'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.warning("⚠️ No autorizado para obtener perfil del asesor")
            return None
        else:
            st.error(f"Error al obtener perfil del asesor: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener perfil del asesor: {str(e)}")
        return None

def obtener_puede_operar(token_portador):
    """Obtiene si el usuario puede operar"""
    url = 'https://api.invertironline.com/api/v2/operar/CPD/PuedeOperar'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al verificar si puede operar: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error al verificar si puede operar: {str(e)}")
        return None

def obtener_estado_segmento(token_portador, estado, segmento):
    """Obtiene el estado de un segmento específico"""
    url = f'https://api.invertironline.com/api/v2/operar/CPD/{estado}/{segmento}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado del segmento: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error al obtener estado del segmento: {str(e)}")
        return None

def obtener_comisiones_cpd(token_portador, importe, plazo, tasa):
    """Obtiene las comisiones para CPD"""
    url = f'https://api.invertironline.com/api/v2/operar/CPD/Comisiones/{importe}/{plazo}/{tasa}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener comisiones CPD: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error al obtener comisiones CPD: {str(e)}")
        return None

def operar_cpd(token_portador, datos_operacion):
    """Realiza una operación de CPD"""
    url = 'https://api.invertironline.com/api/v2/operar/CPD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_operacion, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al operar CPD: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al operar CPD: {str(e)}")
        return None

def operar_token(token_portador, datos_operacion):
    """Realiza una operación de token"""
    url = 'https://api.invertironline.com/api/v2/operar/Token'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_operacion, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al operar token: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al operar token: {str(e)}")
        return None
                
def vender_activo(token_portador, datos_venta):
    """Realiza una venta de activo"""
    url = 'https://api.invertironline.com/api/v2/operar/Vender'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_venta, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al vender activo: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error al vender activo: {str(e)}")
        return None

def comprar_activo(token_portador, datos_compra):
    """Realiza una compra de activo"""
    url = 'https://api.invertironline.com/api/v2/operar/Comprar'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_compra, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al comprar activo: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error al comprar activo: {str(e)}")
        return None

def rescate_fci(token_portador, datos_rescate):
    """Realiza un rescate de FCI"""
    url = 'https://api.invertironline.com/api/v2/operar/rescate/fci'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_rescate, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al rescatar FCI: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al rescatar FCI: {str(e)}")
        return None

def vender_especie_d(token_portador, datos_venta):
    """Realiza una venta de especie D"""
    url = 'https://api.invertironline.com/api/v2/operar/VenderEspecieD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_venta, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al vender especie D: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al vender especie D: {str(e)}")
        return None
    
def comprar_especie_d(token_portador, datos_compra):
    """Realiza una compra de especie D"""
    url = 'https://api.invertironline.com/api/v2/operar/ComprarEspecieD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_compra, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al comprar especie D: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al comprar especie D: {str(e)}")
        return None

def suscripcion_fci(token_portador, datos_suscripcion):
    """Realiza una suscripción a FCI"""
    url = 'https://api.invertironline.com/api/v2/operar/suscripcion/fci'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_suscripcion, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al suscribir FCI: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al suscribir FCI: {str(e)}")
        return None

# Funciones de Operatoria Simplificada
def obtener_montos_estimados(token_portador, monto):
    """Obtiene montos estimados para operatoria simplificada"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/MontosEstimados/{monto}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener montos estimados: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener montos estimados: {str(e)}")
        return None

def obtener_parametros_operatoria(token_portador, id_tipo_operatoria):
    """Obtiene parámetros para un tipo de operatoria"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/{id_tipo_operatoria}/Parametros'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener parámetros de operatoria: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener parámetros de operatoria: {str(e)}")
        return None

def validar_operatoria(token_portador, monto, id_tipo_operatoria):
    """Valida una operatoria simplificada"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/Validar/{monto}/{id_tipo_operatoria}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al validar operatoria: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error al validar operatoria: {str(e)}")
        return None

def obtener_montos_estimados_venta_mep(token_portador, monto):
    """Obtiene montos estimados para venta MEP simple"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/VentaMepSimple/MontosEstimados/{monto}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener montos estimados venta MEP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener montos estimados venta MEP: {str(e)}")
        return None

def obtener_cotizaciones_mep(token_portador):
    """Obtiene cotizaciones MEP"""
    url = 'https://api.invertironline.com/api/v2/Cotizaciones/MEP'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotizaciones MEP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener cotizaciones MEP: {str(e)}")
        return None
        
def comprar_operatoria_simplificada(token_portador, datos_compra):
    """Realiza una compra usando operatoria simplificada"""
    url = 'https://api.invertironline.com/api/v2/OperatoriaSimplificada/Comprar'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_compra, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al comprar con operatoria simplificada: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al comprar con operatoria simplificada: {str(e)}")
        return None

# Funciones del Test del Inversor para Asesores
def obtener_test_inversor(token_portador):
    """Obtiene el test del inversor del asesor"""
    url = 'https://api.invertironline.com/api/v2/asesores/test-inversor'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener test del inversor: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener test del inversor: {str(e)}")
        return None

def enviar_test_inversor(token_portador, datos_test):
    """Envía el test del inversor del asesor"""
    url = 'https://api.invertironline.com/api/v2/asesores/test-inversor'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_test, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al enviar test del inversor: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al enviar test del inversor: {str(e)}")
        return None

def enviar_test_inversor_cliente(token_portador, id_cliente_asesorado, datos_test):
    """Envía el test del inversor para un cliente específico"""
    url = f'https://api.invertironline.com/api/v2/asesores/test-inversor/{id_cliente_asesorado}'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        response = requests.post(url, headers=headers, json=datos_test, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al enviar test del inversor para cliente {id_cliente_asesorado}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al enviar test del inversor para cliente {id_cliente_asesorado}: {str(e)}")
        return None

# --- Nuevas funciones de API para operaciones y detalles ---

def obtener_detalle_operacion(token_portador, numero_operacion):
    """Obtiene el detalle de una operación específica por número"""
    url = f'https://api.invertironline.com/api/v2/operaciones/{numero_operacion}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener detalle de operación {numero_operacion}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener detalle de operación {numero_operacion}: {str(e)}")
        return None

def obtener_operaciones_filtradas(token_portador, numero=None, estado=None, fecha_desde=None, fecha_hasta=None, pais="argentina"):
    """Obtiene operaciones con filtros avanzados"""
    url = 'https://api.invertironline.com/api/v2/operaciones'
    headers = obtener_encabezado_autorizacion(token_portador)
    params = {}
    
    if numero:
        params['filtro.numero'] = numero
    if estado:
        params['filtro.estado'] = estado
    if fecha_desde:
        params['filtro.fechaDesde'] = fecha_desde
    if fecha_hasta:
        params['filtro.fechaHasta'] = fecha_hasta
    if pais:
        params['filtro.pais'] = pais
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener operaciones filtradas: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener operaciones filtradas: {str(e)}")
        return []

def obtener_movimientos_asesor(token_portador, clientes=None, fecha_desde=None, fecha_hasta=None, 
                              tipo_fecha=None, estado=None, tipo=None, pais=None, moneda=None, cuenta_comitente=None):
    """Obtiene movimientos para asesores con filtros avanzados"""
    url = 'https://api.invertironline.com/api/v2/Asesor/Movimientos'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {}
    if clientes:
        data['clientes'] = clientes
    if fecha_desde:
        data['from'] = fecha_desde
    if fecha_hasta:
        data['to'] = fecha_hasta
    if tipo_fecha:
        data['dateType'] = tipo_fecha
    if estado:
        data['status'] = estado
    if tipo:
        data['type'] = tipo
    if pais:
        data['country'] = pais
    if moneda:
        data['currency'] = moneda
    if cuenta_comitente:
        data['cuentaComitente'] = cuenta_comitente
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener movimientos del asesor: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error al obtener movimientos del asesor: {str(e)}")
        return {}

# --- Funciones de operaciones CPD ---

def obtener_estado_segmento_cpd(token_portador, estado, segmento):
    """Obtiene el estado de un segmento CPD específico"""
    url = f'https://api.invertironline.com/api/v2/operar/CPD/{estado}/{segmento}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado CPD {estado}/{segmento}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener estado CPD {estado}/{segmento}: {str(e)}")
        return None

def obtener_comisiones_cpd(token_portador, importe, plazo, tasa):
    """Obtiene las comisiones para operaciones CPD"""
    url = f'https://api.invertironline.com/api/v2/operar/CPD/Comisiones/{importe}/{plazo}/{tasa}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener comisiones CPD: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener comisiones CPD: {str(e)}")
        return None

def operar_cpd(token_portador, id_subasta, tasa, fuente="compra_Venta_Por_Web"):
    """Realiza una operación CPD"""
    url = 'https://api.invertironline.com/api/v2/operar/CPD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "idSubasta": id_subasta,
        "tasa": tasa,
        "fuente": fuente
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al operar CPD: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al operar CPD: {str(e)}")
        return None

# --- Funciones de operaciones Token ---

def operar_token(token_portador, mercado, simbolo, cantidad, monto):
    """Realiza una operación con token"""
    url = 'https://api.invertironline.com/api/v2/operar/Token'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "monto": monto
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al operar con token: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al operar con token: {str(e)}")
        return None

# --- Funciones de operaciones de compra/venta ---

def vender_activo(token_portador, mercado, simbolo, cantidad, precio, validez, tipo_orden="precioLimite", plazo="t0", id_fuente=0):
    """Vende un activo"""
    url = 'https://api.invertironline.com/api/v2/operar/Vender'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "validez": validez,
        "tipoOrden": tipo_orden,
        "plazo": plazo,
        "idFuente": id_fuente
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al vender activo: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al vender activo: {str(e)}")
        return None

def comprar_activo(token_portador, mercado, simbolo, cantidad, precio, plazo, validez, tipo_orden="precioLimite", monto=0, id_fuente=0):
    """Compra un activo"""
    url = 'https://api.invertironline.com/api/v2/operar/Comprar'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "plazo": plazo,
        "validez": validez,
        "tipoOrden": tipo_orden,
        "monto": monto,
        "idFuente": id_fuente
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al comprar activo: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al comprar activo: {str(e)}")
        return None

# --- Funciones de operaciones FCI ---

def rescate_fci(token_portador, simbolo, cantidad, solo_validar=True):
    """Realiza un rescate de FCI"""
    url = 'https://api.invertironline.com/api/v2/operar/rescate/fci'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "simbolo": simbolo,
        "cantidad": cantidad,
        "soloValidar": solo_validar
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al rescatar FCI: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al rescatar FCI: {str(e)}")
        return None

def suscripcion_fci(token_portador, simbolo, monto, solo_validar=True):
    """Realiza una suscripción a FCI"""
    url = 'https://api.invertironline.com/api/v2/operar/suscripcion/fci'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "simbolo": simbolo,
        "monto": monto,
        "soloValidar": solo_validar
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al suscribir FCI: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al suscribir FCI: {str(e)}")
        return None

# --- Funciones de operaciones Especie D ---

def vender_especie_d(token_portador, mercado, simbolo, cantidad, precio, validez, id_cuenta_bancaria=0, tipo_orden="precioLimite", plazo="t0", id_fuente=0):
    """Vende una especie D"""
    url = 'https://api.invertironline.com/api/v2/operar/VenderEspecieD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "validez": validez,
        "idCuentaBancaria": id_cuenta_bancaria,
        "tipoOrden": tipo_orden,
        "plazo": plazo,
        "idFuente": id_fuente
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al vender especie D: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al vender especie D: {str(e)}")
        return None

def comprar_especie_d(token_portador, mercado, simbolo, cantidad, precio, plazo, validez, tipo_orden="precioLimite", monto=0, id_fuente=0):
    """Compra una especie D"""
    url = 'https://api.invertironline.com/api/v2/operar/ComprarEspecieD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "plazo": plazo,
        "validez": validez,
        "tipoOrden": tipo_orden,
        "monto": monto,
        "idFuente": id_fuente
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al comprar especie D: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al comprar especie D: {str(e)}")
        return None

# --- Funciones de operaciones para asesores ---

def vender_especie_d_asesor(token_portador, id_cliente_asesorado, fondos_operacion, mercado, simbolo, cantidad, precio, validez, id_cuenta_bancaria=0, tipo_orden="precioLimite", plazo="t0", id_fuente=0):
    """Vende una especie D para un cliente asesorado"""
    url = 'https://api.invertironline.com/api/v2/asesores/operar/VenderEspecieD'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "idClienteAsesorado": id_cliente_asesorado,
        "fondosParaOperacion": fondos_operacion,
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "validez": validez,
        "idCuentaBancaria": id_cuenta_bancaria,
        "tipoOrden": tipo_orden,
        "plazo": plazo,
        "idFuente": id_fuente
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al vender especie D para cliente {id_cliente_asesorado}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al vender especie D para cliente {id_cliente_asesorado}: {str(e)}")
        return None

# --- Funciones de Operatoria Simplificada ---

def obtener_montos_estimados(token_portador, monto):
    """Obtiene montos estimados para operatoria simplificada"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/MontosEstimados/{monto}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener montos estimados: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener montos estimados: {str(e)}")
        return None

def obtener_parametros_operatoria(token_portador, id_tipo_operatoria):
    """Obtiene parámetros para un tipo de operatoria simplificada"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/{id_tipo_operatoria}/Parametros'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener parámetros de operatoria: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener parámetros de operatoria: {str(e)}")
        return None

def validar_operatoria(token_portador, monto, id_tipo_operatoria):
    """Valida una operatoria simplificada"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/Validar/{monto}/{id_tipo_operatoria}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al validar operatoria: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al validar operatoria: {str(e)}")
        return None

def obtener_montos_estimados_venta_mep(token_portador, monto):
    """Obtiene montos estimados para venta MEP simplificada"""
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/VentaMepSimple/MontosEstimados/{monto}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener montos estimados venta MEP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener montos estimados venta MEP: {str(e)}")
        return None

def obtener_cotizaciones_mep(token_portador, simbolo, id_plazo_operatoria_compra, id_plazo_operatoria_venta):
    """Obtiene cotizaciones MEP"""
    url = 'https://api.invertironline.com/api/v2/Cotizaciones/MEP'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "simbolo": simbolo,
        "idPlazoOperatoriaCompra": id_plazo_operatoria_compra,
        "idPlazoOperatoriaVenta": id_plazo_operatoria_venta
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotizaciones MEP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener cotizaciones MEP: {str(e)}")
        return None

def comprar_operatoria_simplificada(token_portador, monto, id_tipo_operatoria_simplificada, id_cuenta_bancaria=0):
    """Realiza una compra con operatoria simplificada"""
    url = 'https://api.invertironline.com/api/v2/OperatoriaSimplificada/Comprar'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    data = {
        "monto": monto,
        "idTipoOperatoriaSimplificada": id_tipo_operatoria_simplificada,
        "idCuentaBancaria": id_cuenta_bancaria
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al comprar con operatoria simplificada: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al comprar con operatoria simplificada: {str(e)}")
        return None

# --- Funciones de Cotizaciones y Títulos ---

def obtener_cotizacion_mep_simbolo(token_portador, simbolo):
    """Obtiene cotización MEP para un símbolo específico"""
    url = f'https://api.invertironline.com/api/v2/Cotizaciones/MEP/{simbolo}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotización MEP para {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener cotización MEP para {simbolo}: {str(e)}")
        return None

def obtener_cotizacion_historica_mep(token_portador, simbolo, fecha_desde, fecha_hasta):
    """Obtiene cotizaciones históricas MEP para un símbolo"""
    url = f'https://api.invertironline.com/api/v2/{simbolo}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/false'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotizaciones históricas MEP para {simbolo}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener cotizaciones históricas MEP para {simbolo}: {str(e)}")
        return []

def obtener_fci_lista(token_portador):
    """Obtiene la lista de FCI disponibles"""
    url = 'https://api.invertironline.com/api/v2/Titulos/FCI'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener lista de FCI: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener lista de FCI: {str(e)}")
        return []

def obtener_fci_detalle(token_portador, simbolo):
    """Obtiene detalles de un FCI específico"""
    url = f'https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener detalle del FCI {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener detalle del FCI {simbolo}: {str(e)}")
        return None

def obtener_tipos_fondos(token_portador):
    """Obtiene los tipos de fondos disponibles"""
    url = 'https://api.invertironline.com/api/v2/Titulos/FCI/TipoFondos'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener tipos de fondos: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener tipos de fondos: {str(e)}")
        return []

def obtener_cotizacion_titulo(token_portador, mercado, simbolo):
    """Obtiene cotización de un título específico"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotización de {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener cotización de {simbolo}: {str(e)}")
        return None

def obtener_cotizaciones_historica(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="false"):
    """Obtiene cotizaciones históricas de un título"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotizaciones históricas de {simbolo}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener cotizaciones históricas de {simbolo}: {str(e)}")
        return []

def obtener_administradoras_fci(token_portador):
    """Obtiene las administradoras de FCI disponibles"""
    url = 'https://api.invertironline.com/api/v2/Titulos/FCI/Administradoras'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener administradoras de FCI: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener administradoras de FCI: {str(e)}")
        return []

def obtener_detalle_titulo(token_portador, mercado, simbolo):
    """Obtiene detalles de un título específico"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener detalle del título {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener detalle del título {simbolo}: {str(e)}")
        return None

def obtener_opciones_titulo(token_portador, mercado, simbolo):
    """Obtiene opciones de un título específico"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Opciones'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener opciones del título {simbolo}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener opciones del título {simbolo}: {str(e)}")
        return []

def obtener_instrumentos_pais(token_portador, pais, instrumento=None):
    """Obtiene instrumentos por país"""
    url = f'https://api.invertironline.com/api/v2/{pais}/Titulos/Cotizacion/Instrumentos'
    headers = obtener_encabezado_autorizacion(token_portador)
    params = {}
    
    if instrumento:
        params['instrumento'] = instrumento
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener instrumentos del país {pais}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener instrumentos del país {pais}: {str(e)}")
        return []

def obtener_cotizacion_detalle(token_portador, mercado, simbolo):
    """Obtiene cotización detallada de un título"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotización detallada de {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener cotización detallada de {simbolo}: {str(e)}")
        return None

def obtener_administradoras_fci(token_portador):
    """Obtiene las administradoras de FCI disponibles"""
    url = 'https://api.invertironline.com/api/v2/Titulos/FCI/Administradoras'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener administradoras de FCI: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener administradoras de FCI: {str(e)}")
        return []

def obtener_detalle_titulo(token_portador, mercado, simbolo):
    """Obtiene detalles de un título específico"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener detalle del título {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error al obtener detalle del título {simbolo}: {str(e)}")
        return None

def obtener_opciones_titulo(token_portador, mercado, simbolo):
    """Obtiene opciones de un título específico"""
    url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Opciones'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener opciones del título {simbolo}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener opciones del título {simbolo}: {str(e)}")
        return []

def obtener_instrumentos_por_pais(token_portador, pais):
    """Obtiene instrumentos por país"""
    url = f'https://api.invertironline.com/api/v2/{pais}/Titulos/Cotizacion/Instrumentos'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener instrumentos de {pais}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error al obtener instrumentos de {pais}: {str(e)}")
        return []

# --- Funciones de Interfaz para Cotizaciones ---

def mostrar_panel_cotizaciones(token_portador):
    """Muestra el panel de cotizaciones y datos"""
    st.markdown("### 💱 Panel de Cotizaciones y Datos")
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3, tab4 = st.tabs(["🇺🇸 Dólar MEP", "📊 FCI", "📈 Cotizaciones", "💰 Estado USD"])
    
    with tab1:
        mostrar_cotizaciones_mep(token_portador)
    
    with tab2:
        mostrar_panel_fci(token_portador)
    
    with tab3:
        mostrar_cotizaciones_generales(token_portador)
    
    with tab4:
        mostrar_estado_usd(token_portador)

def mostrar_cotizaciones_mep(token_portador):
    """Muestra cotizaciones del dólar MEP"""
    st.markdown("#### 🇺🇸 Cotizaciones Dólar MEP")
    
    # Simbolos comunes para MEP
    simbolos_mep = ["GGAL", "PAMP", "TXAR", "MIRG", "IRSA"]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        simbolo_seleccionado = st.selectbox(
            "Seleccionar símbolo MEP",
            simbolos_mep,
            help="Selecciona un símbolo para ver su cotización MEP"
        )
    
    with col2:
        if st.button("🔄 Actualizar Cotización", type="primary"):
            st.rerun()
    
    # Obtener cotización actual
    with st.spinner("Obteniendo cotización MEP..."):
        cotizacion = obtener_cotizacion_mep_simbolo(token_portador, simbolo_seleccionado)
    
    if cotizacion:
        st.success(f"✅ Cotización MEP {simbolo_seleccionado}: ${cotizacion:.2f}")
        
        # Mostrar gráfico histórico
        st.markdown("#### 📈 Evolución Histórica")
        
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))
        with col_fecha2:
            fecha_hasta = st.date_input("Hasta", value=date.today())
        
        if st.button("📊 Generar Gráfico Histórico"):
            with st.spinner("Obteniendo datos históricos..."):
                datos_historicos = obtener_cotizaciones_historica(
                    token_portador, "bCBA", simbolo_seleccionado, 
                    fecha_desde.strftime('%Y-%m-%d'), 
                    fecha_hasta.strftime('%Y-%m-%d')
                )
            
            if datos_historicos:
                df_historico = pd.DataFrame(datos_historicos)
                if not df_historico.empty:
                    fig = px.line(
                        df_historico, 
                        x='fecha', 
                        y='ultimoPrecio',
                        title=f"Evolución Histórica {simbolo_seleccionado}",
                        labels={'ultimoPrecio': 'Precio ($)', 'fecha': 'Fecha'}
                    )
                    fig.update_layout(
                        xaxis_title="Fecha",
                        yaxis_title="Precio ($)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"mep_hist_{simbolo_seleccionado}")
                else:
                    st.warning("No hay datos históricos disponibles para el período seleccionado")
            else:
                st.error("No se pudieron obtener los datos históricos")
    else:
        st.error("No se pudo obtener la cotización MEP")

def mostrar_panel_fci(token_portador):
    """Muestra panel de FCI"""
    st.markdown("#### 📊 Fondos Comunes de Inversión")
    
    # Obtener lista de FCI
    with st.spinner("Cargando FCI..."):
        fci_lista = obtener_fci_lista(token_portador)
    
    if fci_lista:
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtrar por tipo de fondo
            tipos_fondos = obtener_tipos_fondos(token_portador)
            if tipos_fondos:
                tipo_seleccionado = st.selectbox(
                    "Filtrar por tipo de fondo",
                    ["Todos"] + [tipo["nombre"] for tipo in tipos_fondos],
                    help="Selecciona un tipo de fondo para filtrar"
                )
            else:
                tipo_seleccionado = "Todos"
        
        with col2:
            # Buscar FCI específico
            simbolo_buscar = st.text_input("Buscar FCI por símbolo", placeholder="Ej: ALFA")
        
        # Filtrar FCI
        fci_filtrados = fci_lista
        if tipo_seleccionado != "Todos":
            fci_filtrados = [fci for fci in fci_filtrados if fci.get("tipoFondo") == tipo_seleccionado.lower().replace(" ", "_")]
        
        if simbolo_buscar:
            fci_filtrados = [fci for fci in fci_filtrados if simbolo_buscar.upper() in fci.get("simbolo", "").upper()]
        
        # Mostrar tabla de FCI
        if fci_filtrados:
            df_fci = pd.DataFrame(fci_filtrados)
            
            # Seleccionar columnas importantes
            columnas_mostrar = ["simbolo", "descripcion", "ultimoOperado", "variacion", "variacionMensual", "tipoFondo"]
            columnas_disponibles = [col for col in columnas_mostrar if col in df_fci.columns]
            
            if columnas_disponibles:
                st.dataframe(
                    df_fci[columnas_disponibles],
                    use_container_width=True,
                    height=400
                )
                
                # Mostrar detalles de FCI seleccionado
                st.markdown("#### 📋 Detalles del FCI")
                simbolos_disponibles = df_fci["simbolo"].tolist()
                fci_seleccionado = st.selectbox("Seleccionar FCI para ver detalles", simbolos_disponibles)
                
                if st.button("📊 Ver Detalles"):
                    with st.spinner("Obteniendo detalles del FCI..."):
                        detalle_fci = obtener_fci_detalle(token_portador, fci_seleccionado)
                    
                    if detalle_fci:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("💰 Último Operado", f"${detalle_fci.get('ultimoOperado', 0):.2f}")
                            st.metric("📈 Variación Diaria", f"{detalle_fci.get('variacion', 0):.2f}%")
                            st.metric("📊 Variación Mensual", f"{detalle_fci.get('variacionMensual', 0):.2f}%")
                        
                        with col2:
                            st.metric("📅 Variación Anual", f"{detalle_fci.get('variacionAnual', 0):.2f}%")
                            st.metric("💵 Monto Mínimo", f"${detalle_fci.get('montoMinimo', 0):.2f}")
                            st.metric("⏰ Rescate", detalle_fci.get('rescate', 'N/A'))
                        
                        st.markdown(f"**Descripción:** {detalle_fci.get('descripcion', 'N/A')}")
                        st.markdown(f"**Horizonte:** {detalle_fci.get('horizonteInversion', 'N/A')}")
                        st.markdown(f"**Perfil Inversor:** {detalle_fci.get('perfilInversor', 'N/A')}")
        else:
            st.warning("No se encontraron FCI con los filtros aplicados")
    else:
        st.error("No se pudieron obtener los FCI")

def mostrar_cotizaciones_generales(token_portador):
    """Muestra cotizaciones generales"""
    st.markdown("#### 📈 Cotizaciones Generales")
    
    # Simbolos populares
    simbolos_populares = {
        "Acciones": ["GGAL", "PAMP", "TXAR", "MIRG", "IRSA", "ALUA", "BBAR"],
        "Bonos": ["GD30", "GD35", "AL30", "AE38", "AL35"],
        "CEDEARs": ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN"]
    }
    
    categoria = st.selectbox("Seleccionar categoría", list(simbolos_populares.keys()))
    simbolo_seleccionado = st.selectbox("Seleccionar símbolo", simbolos_populares[categoria])
    
    mercado = "bCBA"  # Por defecto
    
    if st.button("📊 Obtener Cotización"):
        with st.spinner("Obteniendo cotización..."):
            cotizacion = obtener_cotizacion_titulo(token_portador, mercado, simbolo_seleccionado)
        
        if cotizacion:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Último Precio", f"${cotizacion.get('ultimoPrecio', 0):.2f}")
            with col2:
                st.metric("📈 Variación", f"{cotizacion.get('variacion', 0):.2f}%")
            with col3:
                st.metric("📊 Volumen", f"{cotizacion.get('volumenNominal', 0):,.0f}")
            
            # Gráfico histórico
            st.markdown("#### 📈 Evolución Histórica")
            
            col_fecha1, col_fecha2 = st.columns(2)
            with col_fecha1:
                fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30), key="fecha_desde_gen")
            with col_fecha2:
                fecha_hasta = st.date_input("Hasta", value=date.today(), key="fecha_hasta_gen")
            
            if st.button("📊 Generar Gráfico"):
                with st.spinner("Obteniendo datos históricos..."):
                    datos_historicos = obtener_cotizaciones_historica(
                        token_portador, mercado, simbolo_seleccionado,
                        fecha_desde.strftime('%Y-%m-%d'),
                        fecha_hasta.strftime('%Y-%m-%d')
                    )
                
                if datos_historicos:
                    df_historico = pd.DataFrame(datos_historicos)
                    if not df_historico.empty:
                        fig = px.line(
                            df_historico,
                            x='fecha',
                            y='ultimoPrecio',
                            title=f"Evolución Histórica {simbolo_seleccionado}",
                            labels={'ultimoPrecio': 'Precio ($)', 'fecha': 'Fecha'}
                        )
                        fig.update_layout(
                            xaxis_title="Fecha",
                            yaxis_title="Precio ($)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"cotiz_gen_{simbolo_seleccionado}")
                    else:
                        st.warning("No hay datos históricos disponibles")
                else:
                    st.error("No se pudieron obtener los datos históricos")
        else:
            st.error("No se pudo obtener la cotización")

def mostrar_estado_usd(token_portador):
    """Muestra estado de cuenta en USD y botones de compra/venta"""
    st.markdown("#### 💰 Estado de Cuenta USD")
    
    # Obtener estado de cuenta
    with st.spinner("Obteniendo estado de cuenta..."):
        estado_cuenta = obtener_estado_cuenta(token_portador)
    
    if estado_cuenta:
        # Filtrar cuentas USD
        cuentas_usd = []
        if 'cuentas' in estado_cuenta:
            cuentas_usd = [cuenta for cuenta in estado_cuenta['cuentas'] if cuenta.get('moneda') == 'dolar_Estadounidense']
        
        if cuentas_usd:
            st.markdown("##### 💵 Cuentas en USD")
            
            for cuenta in cuentas_usd:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💵 Disponible", f"USD ${cuenta.get('disponible', 0):.2f}")
                with col2:
                    st.metric("📊 Comprometido", f"USD ${cuenta.get('comprometido', 0):.2f}")
                with col3:
                    st.metric("💰 Total", f"USD ${cuenta.get('total', 0):.2f}")
                
                st.markdown(f"**Tipo:** {cuenta.get('tipo', 'N/A')}")
                st.markdown(f"**Estado:** {cuenta.get('estado', 'N/A')}")
                st.markdown("---")
            
            # Botones de compra/venta USD
            st.markdown("##### 🔄 Operaciones USD")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**💵 Comprar USD**")
                with st.form("comprar_usd_form"):
                    monto_compra = st.number_input("Monto en ARS", min_value=0.0, step=1000.0, key="monto_compra")
                    simbolo_mep = st.selectbox("Símbolo MEP", ["GGAL", "PAMP", "TXAR", "MIRG"], key="simbolo_compra")
                    
                    if st.form_submit_button("💵 Comprar USD", type="primary"):
                        st.success(f"✅ Orden de compra de USD por ${monto_compra:.2f} ARS enviada")
                        # Aquí se implementaría la lógica de compra real
            
            with col2:
                st.markdown("**💰 Vender USD**")
                with st.form("vender_usd_form"):
                    monto_venta = st.number_input("Monto en USD", min_value=0.0, step=1.0, key="monto_venta")
                    simbolo_mep = st.selectbox("Símbolo MEP", ["GGAL", "PAMP", "TXAR", "MIRG"], key="simbolo_venta")
                    
                    if st.form_submit_button("💰 Vender USD", type="primary"):
                        st.success(f"✅ Orden de venta de USD ${monto_venta:.2f} enviada")
                        # Aquí se implementaría la lógica de venta real
        else:
            st.warning("No se encontraron cuentas en USD")
    else:
        st.error("No se pudo obtener el estado de cuenta")

def calcular_valor_portafolio_historico(token_portador, operaciones, fecha_desde=None, fecha_hasta=None):
    """
    Calcula el valor del portafolio a lo largo del tiempo basado en operaciones históricas
    
    Args:
        token_portador (str): Token de acceso para la autenticación
        operaciones (list): Lista de operaciones obtenidas de la API
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        tuple: (DataFrame con valores del portafolio, posiciones actuales, DataFrame de flujo de efectivo)
    """
    if not operaciones:
        return None, {}, None
    
    # Convertir operaciones a DataFrame
    df_ops = pd.DataFrame(operaciones)
    df_ops['fechaOrden'] = pd.to_datetime(df_ops['fechaOrden'], format='mixed')
    df_ops = df_ops.sort_values('fechaOrden')
    
    # Obtener símbolos únicos
    simbolos = df_ops['simbolo'].unique()
    
    # Calcular posición actual por símbolo y flujo de efectivo
    posiciones = {}
    flujo_efectivo = []
    
    for simbolo in simbolos:
        ops_simbolo = df_ops[df_ops['simbolo'] == simbolo]
        cantidad_total = 0
        
        for _, op in ops_simbolo.iterrows():
            if op['tipo'] == 'Compra':
                cantidad_total += op['cantidadOperada']
                flujo_efectivo.append({
                    'fecha': op['fechaOrden'],
                    'tipo': 'Compra',
                    'simbolo': simbolo,
                    'monto': -op['montoOperado'],  # Salida de efectivo
                    'cantidad': op['cantidadOperada'],
                    'precio': op['precioOperado']
                })
            elif op['tipo'] == 'Venta':
                cantidad_total -= op['cantidadOperada']
                flujo_efectivo.append({
                    'fecha': op['fechaOrden'],
                    'tipo': 'Venta',
                    'simbolo': simbolo,
                    'monto': op['montoOperado'],  # Entrada de efectivo
                    'cantidad': op['cantidadOperada'],
                    'precio': op['precioOperado']
                })
        
        posiciones[simbolo] = cantidad_total
    
    # Crear DataFrame de flujo de efectivo
    df_flujo = pd.DataFrame(flujo_efectivo)
    if not df_flujo.empty:
        df_flujo = df_flujo.sort_values('fecha')
        df_flujo['valor_acumulado'] = df_flujo['monto'].cumsum()
    
    # Crear serie temporal del valor del portafolio
    if fecha_desde:
        fecha_inicio = pd.to_datetime(fecha_desde).date()
    else:
        fecha_inicio = df_ops['fechaOrden'].min().date()
    
    if fecha_hasta:
        fecha_fin = pd.to_datetime(fecha_hasta).date()
    else:
        fecha_fin = datetime.now().date()
    
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    
    valores_portafolio = []
    for fecha in fechas:
        # Buscar el último valor acumulado hasta esa fecha
        if not df_flujo.empty:
            valores_hasta_fecha = df_flujo[df_flujo['fecha'] <= fecha]
            if not valores_hasta_fecha.empty:
                valor = valores_hasta_fecha['valor_acumulado'].iloc[-1]
            else:
                valor = 0
        else:
            valor = 0
        valores_portafolio.append(valor)
    
    # Crear DataFrame final
    df_portafolio = pd.DataFrame({
        'fecha': fechas,
        'valor': valores_portafolio
    })
    
    return df_portafolio, posiciones, df_flujo

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
    st.markdown(f"### 📈 Análisis de Portafolio - {portfolio_id.upper()}" if portfolio_id else "### 📈 Análisis de Portafolio")
    
    # Mostrar información del cliente seleccionado
    if id_cliente:
        cliente_info = st.session_state.get('cliente_seleccionado', {})
        
        # Dashboard compacto del cliente
        st.markdown("### 👤 Dashboard del Cliente")
        
        # Primera fila: Información básica del cliente
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            nombre_completo = cliente_info.get('apellidoYNombre', cliente_info.get('nombre', 'Cliente'))
            st.metric("👤 Cliente", nombre_completo, help="Nombre del cliente")
        
        with col_info2:
            numero_cliente = cliente_info.get('numeroCliente', cliente_info.get('id', 'N/A'))
            st.metric("🆔 ID", numero_cliente, help="ID del cliente")
        
        with col_info3:
            numero_cuenta = cliente_info.get('numeroCuenta', 'N/A')
            st.metric("🏦 Cuenta", numero_cuenta, help="Número de cuenta")
        
        with col_info4:
            st.metric("📊 Mercado", portfolio_id.upper() if portfolio_id else "General", help="Mercado del portafolio")
        
        # Segunda fila: Estado financiero compacto
        st.markdown("### 💰 Estado Financiero")
        
        col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
        
        with col_fin1:
            disponible_ars = cliente_info.get('disponibleOperarPesos', 0)
            st.metric("💵 Disponible ARS", f"AR$ {disponible_ars:,.2f}", help="Dinero disponible en pesos")
        
        with col_fin2:
            disponible_usd = cliente_info.get('disponibleOperarDolares', 0)
            st.metric("💲 Disponible USD", f"USD {disponible_usd:,.2f}", help="Dinero disponible en dólares")
        
        with col_fin3:
            total_portafolio = cliente_info.get('totalPortafolio', 0)
            st.metric("📈 Total Portafolio", f"AR$ {total_portafolio:,.2f}", help="Valor total del portafolio")
        
        with col_fin4:
            total_cuenta = cliente_info.get('totalCuentaValorizado', 0)
            st.metric("💰 Total Cuenta", f"AR$ {total_cuenta:,.2f}", help="Valor total de la cuenta")
        
        # Gráfico compacto de estado financiero
        fin_data = {
            'Métrica': ['Disponible ARS', 'Disponible USD', 'Total Portafolio', 'Total Cuenta'],
            'Valor': [disponible_ars, disponible_usd, total_portafolio, total_cuenta],
            'Color': ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
        }
        
        fig_fin = px.bar(
            pd.DataFrame(fin_data),
            x='Métrica',
            y='Valor',
            color='Métrica',
            title="Resumen Financiero",
            color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
        )
        fig_fin.update_layout(
            height=250,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Valor (AR$)",
            margin=dict(l=0, r=0, t=40, b=0)
        )
        fig_fin.update_xaxes(tickangle=45)
        st.plotly_chart(fig_fin, use_container_width=True, key=f"fig_fin_{portfolio_id}")
    
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
        
        # Dashboard compacto del portafolio
        st.markdown("### 📊 Resumen del Portafolio")
        
        # Métricas compactas del portafolio
        col_port1, col_port2, col_port3, col_port4 = st.columns(4)
        
        with col_port1:
            st.metric("📈 Activos", len(datos_activos), help="Total de posiciones")
        
        with col_port2:
            st.metric("🔤 Símbolos", df_activos['Símbolo'].nunique(), help="Instrumentos únicos")
        
        with col_port3:
            st.metric("🏷️ Tipos", df_activos['Tipo'].nunique(), help="Categorías de activos")
        
        with col_port4:
            st.metric("💰 Valor Total", f"AR$ {valor_total:,.0f}", help="Valor total del portafolio")
        
        if metricas:
            # Dashboard de Riesgo y Rendimiento
            st.markdown("### ⚖️ Análisis de Riesgo y Rendimiento")
            
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
                st.plotly_chart(fig_riesgo, use_container_width=True, key=f"fig_riesgo_{portfolio_id}")
            
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
                st.plotly_chart(fig_escenarios, use_container_width=True, key=f"fig_escenarios_{portfolio_id}")
            
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
                st.plotly_chart(fig_probs, use_container_width=True, key=f"fig_probs_{portfolio_id}")
        
        # Visualizaciones del Portafolio
        st.markdown("### 📊 Visualizaciones del Portafolio")
        
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
                st.plotly_chart(fig_pie, use_container_width=True, key=f"fig_pie_{portfolio_id}")
                
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
                st.plotly_chart(fig_bars, use_container_width=True, key=f"fig_bars_{portfolio_id}")
            
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
                    st.plotly_chart(fig_hist, use_container_width=True, key=f"fig_hist_{portfolio_id}")
                    
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
                    st.plotly_chart(fig_box, use_container_width=True, key=f"fig_box_{portfolio_id}")
        
        with tab_analisis:
            # Tabla interactiva con Streamlit estándar
            if len(df_activos) > 0:
                # Preparar datos para la tabla
                df_display = df_activos.copy()
                df_display['Peso (%)'] = (df_display['Valuación'] / valor_total * 100).round(2)
                df_display['Valuación'] = df_display['Valuación'].apply(lambda x: f"AR$ {x:,.2f}")
                
                st.markdown("### 📋 Tabla Detallada de Activos")
                
                # Opciones de filtrado
                col_filtro1, col_filtro2 = st.columns(2)
                with col_filtro1:
                    tipo_filtro = st.selectbox("Filtrar por Tipo", ["Todos"] + list(df_display['Tipo'].unique()))
                with col_filtro2:
                    min_valor = st.number_input("Valor Mínimo (AR$)", min_value=0, value=0)
                
                # Aplicar filtros
                df_filtrado = df_display.copy()
                if tipo_filtro != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_filtro]
                df_filtrado = df_filtrado[df_filtrado['Valuación'].str.replace('AR$ ', '').str.replace(',', '').astype(float) >= min_valor]
                
                # Mostrar tabla con estilos
                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    height=400,
                    column_config={
                        "Símbolo": st.column_config.TextColumn("Símbolo", width="small"),
                        "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
                        "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                        "Cantidad": st.column_config.NumberColumn("Cantidad", format="%.2f"),
                        "Precio": st.column_config.NumberColumn("Precio", format="AR$ %.2f"),
                        "Valuación": st.column_config.TextColumn("Valuación", width="small"),
                        "Peso (%)": st.column_config.NumberColumn("Peso (%)", format="%.2f%%")
                    }
                )
                
                # Estadísticas resumen
                st.markdown("#### 📊 Estadísticas Resumen")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                
                with col_stats1:
                    st.metric("Total Activos", len(df_filtrado))
                with col_stats2:
                    valor_filtrado = df_filtrado['Valuación'].str.replace('AR$ ', '').str.replace(',', '').astype(float).sum()
                    st.metric("Valor Filtrado", f"AR$ {valor_filtrado:,.2f}")
                with col_stats3:
                    peso_filtrado = df_filtrado['Peso (%)'].sum()
                    st.metric("Peso Total", f"{peso_filtrado:.2f}%")
        
    else:
        st.warning("No se encontraron activos en el portafolio")

def mostrar_notificaciones(notificaciones):
    """
    Muestra las notificaciones del asesor
    
    Args:
        notificaciones (list): Lista de notificaciones
    """
    st.markdown("### 🔔 Notificaciones")
    
    if not notificaciones:
        st.info("No hay notificaciones disponibles")
        return
    
    for i, notif in enumerate(notificaciones):
        with st.expander(f"📢 {notif.get('titulo', 'Notificación')}", expanded=False):
            st.markdown(f"**Mensaje:** {notif.get('mensaje', 'Sin mensaje')}")
            if notif.get('link'):
                st.markdown(f"**Link:** [{notif.get('link')}]({notif.get('link')})")

def mostrar_perfil_asesor(perfil_asesor):
    """
    Muestra el perfil del asesor
    
    Args:
        perfil_asesor (dict): Datos del perfil del asesor
    """
    st.markdown("### 👨‍💼 Perfil del Asesor")
    
    if not perfil_asesor:
        st.info("No hay datos del perfil del asesor disponibles")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("👤 Nombre", f"{perfil_asesor.get('nombre', 'N/A')} {perfil_asesor.get('apellido', 'N/A')}")
        st.metric("🆔 DNI", perfil_asesor.get('dni', 'N/A'))
        st.metric("🏦 Nº Cuenta", perfil_asesor.get('numeroCuenta', 'N/A'))
    
    with col2:
        st.metric("📧 Email", perfil_asesor.get('email', 'N/A'))
        st.metric("⚖️ Perfil Inversor", perfil_asesor.get('perfilInversor', 'N/A'))
        st.metric("🔒 Estado Cuenta", "✅ Abierta" if perfil_asesor.get('cuentaAbierta') else "❌ Cerrada")
    
    # Información adicional
    st.markdown("#### 📋 Información Adicional")
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown(f"**CUIT/CUIL:** {perfil_asesor.get('cuitCuil', 'N/A')}")
        st.markdown(f"**Sexo:** {perfil_asesor.get('sexo', 'N/A')}")
    
    with col4:
        st.markdown(f"**Actualizar DDJJ:** {'✅ Sí' if perfil_asesor.get('actualizarDDJJ') else '❌ No'}")
        st.markdown(f"**Actualizar Test:** {'✅ Sí' if perfil_asesor.get('actualizarTestInversor') else '❌ No'}")
        st.markdown(f"**Actualizar TyC:** {'✅ Sí' if perfil_asesor.get('actualizarTyC') else '❌ No'}")

def mostrar_panel_test_inversor(token_portador, cliente_seleccionado=None):
    """
    Muestra el panel del test del inversor
    
    Args:
        token_portador (str): Token de acceso
        cliente_seleccionado (dict): Datos del cliente seleccionado (opcional)
    """
    st.markdown("### 📊 Test del Inversor")
    
    # Obtener test actual
    with st.spinner("🔄 Cargando test del inversor..."):
        test_actual = obtener_test_inversor(token_portador)
    
    if not test_actual:
        st.warning("No se pudo obtener el test del inversor")
        return
    
    # Mostrar test actual
    st.markdown("#### 📋 Test Actual")
    if isinstance(test_actual, dict):
        # Mostrar perfil sugerido si existe
        if 'perfilSugerido' in test_actual:
            perfil = test_actual['perfilSugerido']
            st.info(f"**Perfil Sugerido:** {perfil.get('nombre', 'N/A')}")
            if 'detalle' in perfil:
                st.write(f"**Detalle:** {perfil['detalle']}")
        
        # Mostrar composición del perfil si existe
        if 'perfilSugerido' in test_actual and 'perfilComposiciones' in test_actual['perfilSugerido']:
            composiciones = test_actual['perfilSugerido']['perfilComposiciones']
            if composiciones:
                st.markdown("**Composición Sugerida:**")
                for comp in composiciones:
                    st.write(f"- {comp.get('nombre', 'N/A')}: {comp.get('porcentaje', 0)}%")
        
        # Mostrar otras secciones del test
        for key, value in test_actual.items():
            if key != 'perfilSugerido':
                if isinstance(value, dict) and 'pregunta' in value:
                    st.markdown(f"**{value['pregunta']}**")
                else:
                    st.markdown(f"**{key}:** {value}")
    else:
        st.json(test_actual)
    
    # Formulario para nuevo test
    st.markdown("#### ✏️ Actualizar Test")
    
    with st.form("test_inversor_form"):
        st.markdown("**Complete el test del inversor:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Instrumentos invertidos anteriormente
            instrumentos_anteriores = st.multiselect(
                "Instrumentos invertidos anteriormente",
                ["Acciones", "Bonos", "FCI", "Opciones", "Futuros", "Crypto"],
                help="Selecciona los instrumentos en los que has invertido"
            )
            
            # Plazo de inversión
            plazo_inversion = st.selectbox(
                "Plazo de inversión preferido",
                ["Corto plazo (< 1 año)", "Mediano plazo (1-3 años)", "Largo plazo (> 3 años)"],
                help="¿Cuánto tiempo planeas mantener tus inversiones?"
            )
            
            # Edad
            edad = st.selectbox(
                "Rango de edad",
                ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
                help="Selecciona tu rango de edad"
            )
            
            # Objetivo de inversión
            objetivo = st.selectbox(
                "Objetivo de inversión",
                ["Preservar capital", "Generar ingresos", "Crecimiento", "Especulación"],
                help="¿Cuál es tu principal objetivo?"
            )
        
        with col2:
            # Niveles de conocimiento
            conocimiento_acciones = st.selectbox(
                "Conocimiento en Acciones",
                ["Ninguno", "Básico", "Intermedio", "Avanzado"],
                help="Nivel de conocimiento en acciones"
            )
            
            conocimiento_bonos = st.selectbox(
                "Conocimiento en Bonos",
                ["Ninguno", "Básico", "Intermedio", "Avanzado"],
                help="Nivel de conocimiento en bonos"
            )
            
            conocimiento_fci = st.selectbox(
                "Conocimiento en FCI",
                ["Ninguno", "Básico", "Intermedio", "Avanzado"],
                help="Nivel de conocimiento en fondos comunes de inversión"
            )
            
            # Pólizas de seguro
            polizas_seguro = st.selectbox(
                "Pólizas de seguro",
                ["Ninguna", "Vida", "Accidentes", "Vida y Accidentes"],
                help="¿Qué pólizas de seguro tienes?"
            )
        
        # Capacidad de ahorro y patrimonio
        col3, col4 = st.columns(2)
        
        with col3:
            capacidad_ahorro = st.selectbox(
                "Capacidad de ahorro mensual",
                ["< $50,000", "$50,000 - $100,000", "$100,000 - $200,000", "> $200,000"],
                help="¿Cuánto puedes ahorrar mensualmente?"
            )
        
        with col4:
            patrimonio_porcentaje = st.selectbox(
                "Porcentaje del patrimonio a invertir",
                ["< 10%", "10-25%", "25-50%", "> 50%"],
                help="¿Qué porcentaje de tu patrimonio estás dispuesto a invertir?"
            )
        
        enviar_email = st.checkbox(
            "Enviar resultados por email",
            value=True,
            help="Recibir los resultados del test por correo electrónico"
        )
        
        # Botones de envío
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            enviar_asesor = st.form_submit_button("📤 Enviar Test del Asesor", type="primary")
        
        with col_btn2:
            if cliente_seleccionado:
                id_cliente = cliente_seleccionado.get('id', cliente_seleccionado.get('numeroCliente'))
                enviar_cliente = st.form_submit_button(f"👤 Enviar Test para Cliente {id_cliente}")
            else:
                enviar_cliente = False
                st.form_submit_button("👤 Enviar Test para Cliente", disabled=True)
        
        # Procesar envíos
        if enviar_asesor:
            # Preparar datos según la estructura de la API
            datos_test = {
                "enviarEmailCliente": enviar_email,
                "instrumentosInvertidosAnteriormente": [1, 2, 3],  # IDs de ejemplo
                "nivelesConocimientoInstrumentos": [1, 2, 3],  # IDs de ejemplo
                "idPlazoElegido": 1,  # ID del plazo seleccionado
                "idEdadElegida": 1,  # ID de la edad seleccionada
                "idObjetivoInversionElegida": 1,  # ID del objetivo seleccionado
                "idPolizaElegida": 1,  # ID de la póliza seleccionada
                "idCapacidadAhorroElegida": 1,  # ID de la capacidad seleccionada
                "idPorcentajePatrimonioDedicado": 1  # ID del porcentaje seleccionado
            }
            
            resultado = enviar_test_inversor(token_portador, datos_test)
            if resultado:
                st.success("✅ Test del asesor enviado correctamente")
                if 'perfilSugerido' in resultado:
                    perfil = resultado['perfilSugerido']
                    st.info(f"**Nuevo Perfil Sugerido:** {perfil.get('nombre', 'N/A')}")
                st.rerun()
            else:
                st.error("❌ Error al enviar test del asesor")
        
        if enviar_cliente and cliente_seleccionado:
            # Preparar datos según la estructura de la API
            datos_test = {
                "enviarEmailCliente": enviar_email,
                "instrumentosInvertidosAnteriormente": [1, 2, 3],  # IDs de ejemplo
                "nivelesConocimientoInstrumentos": [1, 2, 3],  # IDs de ejemplo
                "idPlazoElegido": 1,  # ID del plazo seleccionado
                "idEdadElegida": 1,  # ID de la edad seleccionada
                "idObjetivoInversionElegida": 1,  # ID del objetivo seleccionado
                "idPolizaElegida": 1,  # ID de la póliza seleccionada
                "idCapacidadAhorroElegida": 1,  # ID de la capacidad seleccionada
                "idPorcentajePatrimonioDedicado": 1  # ID del porcentaje seleccionado
            }
            
            resultado = enviar_test_inversor_cliente(token_portador, id_cliente, datos_test)
            if resultado:
                st.success(f"✅ Test enviado correctamente para el cliente {id_cliente}")
                if 'perfilSugerido' in resultado:
                    perfil = resultado['perfilSugerido']
                    st.info(f"**Nuevo Perfil Sugerido:** {perfil.get('nombre', 'N/A')}")
                st.rerun()
            else:
                st.error(f"❌ Error al enviar test para el cliente {id_cliente}")

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

    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))
    id_cliente = cliente.get('id', cliente.get('numeroCliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Obtener fechas del sidebar
    fecha_desde = st.session_state.get('fecha_desde', date.today() - timedelta(days=365))
    fecha_hasta = st.session_state.get('fecha_hasta', date.today())
    
    # Cargar datos una sola vez y cachearlos
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def cargar_datos_completos(token, fecha_desde, fecha_hasta):
        """Carga y cachea todos los datos necesarios"""
        portafolio_ar = obtener_portafolio_argentina(token)
        portafolio_eeuu = obtener_portafolio_eeuu(token)
        estado_cuenta = obtener_estado_cuenta(token)
        
        # Obtener movimientos históricos
        movimientos_ar = obtener_movimientos(token, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'), 'argentina')
        movimientos_eeuu = obtener_movimientos(token, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'), 'estados_Unidos')
        
        # Calcular valor histórico del portafolio
        valor_historico_ar = calcular_valor_portafolio_historico(token, movimientos_ar, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'))
        valor_historico_eeuu = calcular_valor_portafolio_historico(token, movimientos_eeuu, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'))
        
        return (portafolio_ar, portafolio_eeuu, estado_cuenta, 
                movimientos_ar, movimientos_eeuu, 
                valor_historico_ar, valor_historico_eeuu)
    
    # Cargar datos con cache
    with st.spinner("🔄 Cargando datos del cliente y movimientos históricos..."):
        (portafolio_ar, portafolio_eeuu, estado_cuenta, 
         movimientos_ar, movimientos_eeuu, 
         valor_historico_ar, valor_historico_eeuu) = cargar_datos_completos(token_acceso, fecha_desde, fecha_hasta)
    
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
            if estado_cuenta:
                estado_cuenta_ar = filtrar_estado_cuenta_por_moneda(estado_cuenta, "peso_Argentino")
                if estado_cuenta_ar:
                    mostrar_estado_cuenta(estado_cuenta_ar, es_eeuu=False)
                else:
                    st.warning("No se pudo obtener el estado de cuenta de Argentina")
            else:
                st.warning("No se pudo obtener el estado de cuenta")
        
        with col_estado2:
            if estado_cuenta:
                estado_cuenta_eeuu = filtrar_estado_cuenta_por_moneda(estado_cuenta, "dolar_Estadounidense")
                if estado_cuenta_eeuu:
                    mostrar_estado_cuenta(estado_cuenta_eeuu, es_eeuu=True)
                else:
                    st.warning("No se pudo obtener el estado de cuenta de EEUU")
            else:
                st.warning("No se pudo obtener el estado de cuenta")
    
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
    if 'usuario_autenticado' not in st.session_state:
        st.session_state.usuario_autenticado = False
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0; text-align: center;">🔐 Autenticación IOL</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Autenticación con usuario y contraseña
        st.markdown("#### 👤 Credenciales IOL")
        usuario = st.text_input("Usuario", help="Tu usuario de IOL")
        contraseña = st.text_input("Contraseña", type="password", help="Tu contraseña de IOL")
        
        if st.button("🔑 Iniciar Sesión", type="primary"):
            if usuario and contraseña:
                with st.spinner("🔄 Autenticando..."):
                    token_acceso = autenticar_usuario(usuario, contraseña)
                    if token_acceso:
                        st.session_state.token_acceso = token_acceso
                        st.session_state.usuario_autenticado = True
                        st.success("✅ Autenticación exitosa!")
                        st.rerun()
                    else:
                        st.error("❌ Error en la autenticación")
            else:
                st.warning("⚠️ Por favor, ingresa usuario y contraseña")
        
        # Mostrar estado de conexión
        if st.session_state.token_acceso and st.session_state.usuario_autenticado:
            st.success("✅ Conectado a IOL")
            
            # Botón para cerrar sesión
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.token_acceso = None
                st.session_state.usuario_autenticado = False
                st.session_state.cliente_seleccionado = None
                st.rerun()
            
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
    if st.session_state.token_acceso and st.session_state.usuario_autenticado:
        with st.sidebar:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <h3 style="color: white; margin: 0; text-align: center;">🎯 Menú Principal</h3>
            </div>
            """, unsafe_allow_html=True)
            
            opcion = st.selectbox(
                "Seleccione una opción:",
                ["🏠 Inicio", "📊 Análisis de Portafolio", "💱 Panel de Cotizaciones", "💰 Tasas de Caución", "👨‍💼 Panel del Asesor"]
            )

        # Navegación
        if opcion == "🏠 Inicio":
            st.markdown("### 🏠 Bienvenido al IOL Portfolio Analyzer")
            st.info("Selecciona 'Análisis de Portafolio' para comenzar el análisis del cliente seleccionado.")
            
        elif opcion == "📊 Análisis de Portafolio":
            if st.session_state.cliente_seleccionado:
                mostrar_analisis_portafolio()
            else:
                st.warning("⚠️ Por favor, selecciona un cliente primero")
        
        elif opcion == "💱 Panel de Cotizaciones":
            mostrar_panel_cotizaciones(st.session_state.token_acceso)
        
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
