import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import requests
from bs4 import BeautifulSoup
import urllib3
import yfinance as yf
import pandas as pd
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def obtener_variables_bcra():
    """
    Scrapea las principales variables del BCRA desde la web oficial.
    Devuelve un diccionario con los valores más recientes de reservas, dólar oficial, etc.
    Los nombres de variables se normalizan para facilitar el acceso.
    """
    url = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
    variables = {}
    try:
        # Realizar la solicitud HTTP deshabilitando la verificación SSL
        response = requests.get(url, verify=False, timeout=15)
        if response.status_code == 200:
            # Parsear el contenido HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar filas relevantes en las tablas
            rows = soup.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) == 3:  # Verificar que la fila tenga 3 columnas
                    variable = columns[0].get_text(strip=True)
                    fecha = columns[1].get_text(strip=True)
                    valor = columns[2].get_text(strip=True)
                    
                    # Normalización de nombres para acceso sencillo
                    nombre_lower = variable.lower()
                    
                    # Mejorar la detección de variables clave
                    if "reservas internacionales" in nombre_lower:
                        key = "reservas_internacionales"
                    elif "tipo de cambio mayorista" in nombre_lower and "comunicación a 3500" in nombre_lower:
                        key = "dolar_mayorista"
                    elif "tipo de cambio minorista" in nombre_lower and "comunicación b 9791" in nombre_lower:
                        key = "dolar_minorista"
                    elif "tasa de política monetaria" in nombre_lower and "n.a." in nombre_lower:
                        key = "tasa_monetaria_na"
                    elif "tasa de política monetaria" in nombre_lower and "e.a." in nombre_lower:
                        key = "tasa_monetaria_ea"
                    elif "inflación mensual" in nombre_lower:
                        key = "inflacion_mensual"
                    elif "inflación interanual" in nombre_lower:
                        key = "inflacion_interanual"
                    elif "cer" in nombre_lower and "base" in nombre_lower:
                        key = "cer"
                    elif "base monetaria" in nombre_lower and "total" in nombre_lower:
                        key = "base_monetaria"
                    elif "circulación monetaria" in nombre_lower:
                        key = "circulacion_monetaria"
                    elif "uva" in nombre_lower:
                        key = "uva"
                    elif "uvi" in nombre_lower:
                        key = "uvi"
                    elif "icl" in nombre_lower:
                        key = "icl"
                    elif "tamar" in nombre_lower and "bancos privados" in nombre_lower and "n.a." in nombre_lower:
                        key = "tamar_na"
                    elif "badlar" in nombre_lower and "bancos privados" in nombre_lower and "n.a." in nombre_lower:
                        key = "badlar_na"
                    else:
                        # Usar el nombre original como fallback, limpiando caracteres especiales
                        key = variable.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").lower()
                    
                    variables[key] = {
                        "fecha": fecha, 
                        "valor": valor, 
                        "nombre_original": variable
                    }
        else:
            print(f"Error al acceder a la página del BCRA: {response.status_code}")
    except Exception as e:
        print(f"Error al scrapear BCRA: {str(e)}")
    return variables

def obtener_reservas_bcra():
    """
    Obtiene el valor de reservas internacionales del BCRA usando scraping.
    """
    variables = obtener_variables_bcra()
    # Buscar por clave normalizada
    reservas = variables.get("reservas_internacionales", None)
    if reservas:
        valor = reservas["valor"]
        fecha = reservas["fecha"]
        # Formatear el valor para mostrar millones de USD
        try:
            valor_numerico = float(valor.replace(".", "").replace(",", "."))
            valor_formateado = f"USD {valor_numerico:,.0f}M"
        except:
            valor_formateado = f"USD {valor}M"
        
        return {
            "titulo": f"Reservas BCRA ({fecha})",
            "valor": valor_formateado,
            "delta": None
        }
    else:
        return {
            "titulo": "Reservas BCRA",
            "valor": "No disponible",
            "delta": None
        }

def obtener_cotizacion_iol(token_acceso, simbolo, mercado='BCBA'):
    """
    Obtiene la cotización real de un instrumento usando la API de InvertirOnline.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al obtener cotización para {simbolo}: {str(e)}")
        return None

def obtener_cotizacion_detalle(token_acceso, simbolo, mercado='BCBA'):
    """
    Obtiene el detalle de la cotización real de un instrumento usando la API de InvertirOnline.
    Devuelve un diccionario con los datos principales del instrumento.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Extraemos los campos principales del ejemplo de la documentación
        return {
            "simbolo": simbolo,
            "ultimoPrecio": data.get("ultimoPrecio"),
            "variacion": data.get("variacion"),
            "apertura": data.get("apertura"),
            "maximo": data.get("maximo"),
            "minimo": data.get("minimo"),
            "fechaHora": data.get("fechaHora"),
            "tendencia": data.get("tendencia"),
            "cierreAnterior": data.get("cierreAnterior"),
            "montoOperado": data.get("montoOperado"),
            "volumenNominal": data.get("volumenNominal"),
            "precioPromedio": data.get("precioPromedio")
        }
    except Exception as e:
        print(f"Error al obtener detalle de cotización para {simbolo}: {str(e)}")
        return None

def obtener_tasas_caucion_iol(token_acceso, mercado='argentina'):
    """
    Obtiene las tasas de caución reales desde la API de IOL.
    Devuelve una lista de dicts con plazo y tasa.
    """
    try:
        url = f"https://api.invertironline.com/api/v2/Cotizaciones/cauciones/{mercado}/Todos"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_acceso}'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        cauciones = []
        for t in data.get('titulos', []):
            cauciones.append({
                "plazo": t.get("plazo"),
                "tasa": t.get("tasa"),
                "ultimoPrecio": t.get("ultimoPrecio"),
                "simbolo": t.get("simbolo")
            })
        return cauciones
    except Exception as e:
        print(f"Error al obtener tasas de caución: {str(e)}")
        return []

def obtener_cotizacion_ambito():
    """
    Obtiene cotizaciones de dólares desde la API pública de Ámbito Financiero.
    """
    try:
        url = "https://mercados.ambito.com/dolar/informal/variacion"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "blue": {
                    "compra": data.get("compra"),
                    "venta": data.get("venta"),
                    "variacion": data.get("variacion")
                }
            }
    except Exception as e:
        print(f"Error al obtener cotización de Ámbito: {str(e)}")
        return None

def obtener_dolar_api_publica():
    """
    Obtiene cotizaciones de dólares desde la API pública dolarapi.com
    """
    try:
        # Múltiples endpoints para diferentes tipos de dólar
        urls = {
            "oficial": "https://api.dolarapi.com/v1/dolares/oficial",
            "blue": "https://api.dolarapi.com/v1/dolares/blue", 
            "mep": "https://api.dolarapi.com/v1/dolares/bolsa",
            "ccl": "https://api.dolarapi.com/v1/dolares/contadoconliqui",
            "mayorista": "https://api.dolarapi.com/v1/dolares/mayorista"
        }
        
        resultados = {}
        for tipo, url in urls.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    resultados[tipo] = {
                        "compra": data.get("compra"),
                        "venta": data.get("venta"),
                        "fechaActualizacion": data.get("fechaActualizacion")
                    }
            except Exception as e:
                print(f"Error al obtener {tipo}: {str(e)}")
                continue
        
        return resultados
    except Exception as e:
        print(f"Error al obtener cotizaciones de API pública: {str(e)}")
        return {}

def obtener_bonos_yfinance():
    """
    Obtiene precios de bonos argentinos desde Yahoo Finance para calcular MEP y CCL.
    """
    try:
        # Símbolos de bonos argentinos en diferentes mercados
        simbolos_bonos = {
            "AL30": {"local": "AL30.BA", "nyse": "GGAL"},  # AL30 y ADR
            "GD30": {"local": "GD30.BA", "nyse": "GD30"},
            "AL35": {"local": "AL35.BA", "nyse": "AL35"}
        }
        
        resultados = {}
        for bono, simbolos in simbolos_bonos.items():
            try:
                # Obtener precio local (en pesos)
                ticker_local = yf.Ticker(simbolos["local"])
                hist_local = ticker_local.history(period="1d")
                
                if not hist_local.empty:
                    precio_local = hist_local['Close'].iloc[-1]
                    
                    # Obtener precio en USD (si existe)
                    try:
                        ticker_usd = yf.Ticker(simbolos["nyse"])
                        hist_usd = ticker_usd.history(period="1d")
                        if not hist_usd.empty:
                            precio_usd = hist_usd['Close'].iloc[-1]
                            
                            # Calcular MEP/CCL implícito
                            if precio_usd > 0:
                                dolar_implicito = precio_local / precio_usd
                                resultados[bono] = {
                                    "precio_local": precio_local,
                                    "precio_usd": precio_usd,
                                    "dolar_implicito": dolar_implicito
                                }
                    except:
                        # Si no hay precio en USD, solo guardar precio local
                        resultados[bono] = {
                            "precio_local": precio_local,
                            "precio_usd": None,
                            "dolar_implicito": None
                        }
            except Exception as e:
                print(f"Error al obtener {bono}: {str(e)}")
                continue
        
        return resultados
    except Exception as e:
        print(f"Error al obtener bonos de yfinance: {str(e)}")
        return {}

def obtener_dolar_canje():
    """
    Obtiene información sobre el dólar canje desde fuentes públicas.
    """
    try:
        # API alternativa para dólar canje/tarjeta
        url = "https://api.dolarapi.com/v1/dolares/tarjeta"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "valor": data.get("venta"),
                "compra": data.get("compra"),
                "fecha": data.get("fechaActualizacion")
            }
    except Exception as e:
        print(f"Error al obtener dólar canje: {str(e)}")
        
    # Fallback: calcular aproximadamente como oficial + impuestos
    try:
        oficial_data = obtener_dolar_api_publica().get("oficial", {})
        if oficial_data.get("venta"):
            valor_oficial = float(oficial_data["venta"])
            # Dólar tarjeta/canje aproximado: oficial + 75% impuestos
            valor_canje = valor_oficial * 1.75
            return {
                "valor": round(valor_canje, 2),
                "compra": None,
                "fecha": oficial_data.get("fechaActualizacion")
            }
    except:
        pass
    
    return None

def obtener_mep_iol(token_acceso, simbolo="AL30"):
    """
    Obtiene la cotización MEP usando el endpoint específico de IOL.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        url = 'https://api.invertironline.com/api/v2/Cotizaciones/MEP'
        
        # Parámetros para el cálculo MEP
        data = {
            "simbolo": simbolo,
            "idPlazoOperatoriaCompra": 0,  # T+0
            "idPlazoOperatoriaVenta": 1    # T+1
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # La respuesta es directamente el valor del MEP
        mep_valor = response.json()
        
        return {
            "valor": round(float(mep_valor), 2),
            "simbolo": simbolo,
            "fuente": "IOL API MEP"
        }
        
    except Exception as e:
        print(f"Error al obtener MEP de IOL para {simbolo}: {str(e)}")
        return None

def obtener_ccl_desde_acciones_iol(token_acceso):
    """
    Calcula CCL usando acciones argentinas y sus ADRs desde IOL.
    """
    try:
        # Pares de acciones argentinas y sus ADRs
        pares_ccl = [
            {"local": "GGAL", "adr": "GGAL", "ratio": 10},  # Galicia
            {"local": "YPF", "adr": "YPF", "ratio": 1},     # YPF
            {"local": "PAM", "adr": "PAM", "ratio": 25},    # Pampa Energía
            {"local": "BMA", "adr": "BMA", "ratio": 10},    # Banco Macro
            {"local": "SUPV", "adr": "SUPV", "ratio": 5}   # Supervielle
        ]
        
        ccl_valores = []
        
        for par in pares_ccl:
            try:
                # Obtener cotización local (en pesos)
                accion_local = obtener_cotizacion_detalle(token_acceso, par["local"], 'BCBA')
                
                # Obtener cotización ADR (en USD) - usar mercado NYSE
                adr_data = obtener_cotizacion_detalle(token_acceso, par["adr"], 'NYSE')
                
                if accion_local and adr_data and accion_local.get("ultimoPrecio") and adr_data.get("ultimoPrecio"):
                    precio_local = accion_local["ultimoPrecio"]
                    precio_adr_usd = adr_data["ultimoPrecio"]
                    ratio = par["ratio"]
                    
                    # Calcular CCL implícito
                    ccl_implicito = (precio_local / precio_adr_usd) * ratio
                    
                    ccl_valores.append({
                        "valor": ccl_implicito,
                        "simbolo": par["local"],
                        "precio_local": precio_local,
                        "precio_adr": precio_adr_usd,
                        "ratio": ratio
                    })
                    
            except Exception as e:
                print(f"Error al procesar {par['local']}: {str(e)}")
                continue
        
        if ccl_valores:
            # Promediar los valores de CCL obtenidos
            ccl_promedio = sum(item["valor"] for item in ccl_valores) / len(ccl_valores)
            
            return {
                "valor": round(ccl_promedio, 2),
                "cantidad_instrumentos": len(ccl_valores),
                "detalle": ccl_valores,
                "fuente": "IOL API (Acciones/ADRs)"
            }
        
        return None
        
    except Exception as e:
        print(f"Error al calcular CCL desde acciones: {str(e)}")
        return None

def obtener_mep_ccl_iol_completo(token_acceso):
    """
    Obtiene MEP y CCL usando múltiples métodos de la API de IOL.
    """
    resultados = {
        "MEP": {"valor": None, "variacion": None, "fuente": None},
        "CCL": {"valor": None, "variacion": None, "fuente": None}
    }
    
    # 1. Intentar obtener MEP usando endpoint específico
    try:
        # Probar con diferentes bonos para MEP
        bonos_mep = ["AL30", "AL35", "GD30"]
        
        for bono in bonos_mep:
            mep_data = obtener_mep_iol(token_acceso, bono)
            if mep_data and mep_data.get("valor"):
                resultados["MEP"]["valor"] = mep_data["valor"]
                resultados["MEP"]["fuente"] = f"IOL MEP ({bono})"
                break
                
    except Exception as e:
        print(f"Error al obtener MEP directo: {str(e)}")
    
    # 2. Calcular CCL desde acciones/ADRs
    try:
        ccl_data = obtener_ccl_desde_acciones_iol(token_acceso)
        if ccl_data and ccl_data.get("valor"):
            resultados["CCL"]["valor"] = ccl_data["valor"]
            resultados["CCL"]["fuente"] = f"IOL CCL ({ccl_data['cantidad_instrumentos']} instrumentos)"
            
    except Exception as e:
        print(f"Error al calcular CCL: {str(e)}")
    
    # 3. Si no obtuvimos MEP, calcular desde bonos tradicional
    if not resultados["MEP"]["valor"]:
        try:
            al30 = obtener_cotizacion_detalle(token_acceso, 'AL30', 'BCBA')
            if al30 and al30.get("ultimoPrecio"):
                # Asumir paridad aproximada o usar precio directo si está en rango de dólar
                if al30["ultimoPrecio"] > 100:
                    mep_valor = al30["ultimoPrecio"] / 100
                else:
                    mep_valor = al30["ultimoPrecio"]
                
                resultados["MEP"]["valor"] = round(mep_valor, 2)
                resultados["MEP"]["fuente"] = "IOL AL30 (estimado)"
                
                # Calcular variación si tenemos apertura
                if al30.get("apertura"):
                    apertura = al30["apertura"] / 100 if al30["apertura"] > 100 else al30["apertura"]
                    variacion = ((mep_valor - apertura) / apertura) * 100
                    resultados["MEP"]["variacion"] = round(variacion, 2)
                    
        except Exception as e:
            print(f"Error al calcular MEP desde bonos: {str(e)}")
    
    # 4. Si no obtuvimos CCL, intentar con GD30
    if not resultados["CCL"]["valor"]:
        try:
            gd30 = obtener_cotizacion_detalle(token_acceso, 'GD30', 'BCBA')
            if gd30 and gd30.get("ultimoPrecio"):
                if gd30["ultimoPrecio"] > 100:
                    ccl_valor = gd30["ultimoPrecio"] / 100
                else:
                    ccl_valor = gd30["ultimoPrecio"]
                
                resultados["CCL"]["valor"] = round(ccl_valor, 2)
                resultados["CCL"]["fuente"] = "IOL GD30 (estimado)"
                
                # Calcular variación
                if gd30.get("apertura"):
                    apertura = gd30["apertura"] / 100 if gd30["apertura"] > 100 else gd30["apertura"]
                    variacion = ((ccl_valor - apertura) / apertura) * 100
                    resultados["CCL"]["variacion"] = round(variacion, 2)
                    
        except Exception as e:
            print(f"Error al calcular CCL desde bonos: {str(e)}")
    
    return resultados

def obtener_dolares_financieros_completo(token_acceso=None):
    """
    Obtiene cotizaciones de dólares financieros desde múltiples fuentes.
    Combina datos de IOL, APIs públicas y yfinance.
    """
    resultados = {
        "MEP": {"valor": None, "variacion": None, "fuente": None},
        "CCL": {"valor": None, "variacion": None, "fuente": None},
        "Canje": {"valor": None, "variacion": None, "fuente": None},
        "Blue": {"valor": None, "variacion": None, "fuente": None}
    }
    
    # 1. Si tenemos token IOL, usar primero los métodos específicos de IOL
    if token_acceso:
        try:
            mep_ccl_iol = obtener_mep_ccl_iol_completo(token_acceso)
            if mep_ccl_iol["MEP"]["valor"]:
                resultados["MEP"] = mep_ccl_iol["MEP"]
            if mep_ccl_iol["CCL"]["valor"]:
                resultados["CCL"] = mep_ccl_iol["CCL"]
        except Exception as e:
            print(f"Error con métodos IOL específicos: {str(e)}")
    
    # 2. Intentar obtener desde API pública (como fallback o complemento)
    try:
        cotizaciones_api = obtener_dolar_api_publica()
        if cotizaciones_api:
            # Solo usar API pública si no tenemos datos de IOL
            if not resultados["MEP"]["valor"] and "mep" in cotizaciones_api and cotizaciones_api["mep"].get("venta"):
                resultados["MEP"]["valor"] = float(cotizaciones_api["mep"]["venta"])
                resultados["MEP"]["fuente"] = "API Pública"
            
            if not resultados["CCL"]["valor"] and "ccl" in cotizaciones_api and cotizaciones_api["ccl"].get("venta"):
                resultados["CCL"]["valor"] = float(cotizaciones_api["ccl"]["venta"])
                resultados["CCL"]["fuente"] = "API Pública"
            
            if "blue" in cotizaciones_api and cotizaciones_api["blue"].get("venta"):
                resultados["Blue"]["valor"] = float(cotizaciones_api["blue"]["venta"])
                resultados["Blue"]["fuente"] = "API Pública"
    except Exception as e:
        print(f"Error con API pública: {str(e)}")
    
    # 3. Obtener dólar canje
    try:
        canje_data = obtener_dolar_canje()
        if canje_data and canje_data.get("valor"):
            resultados["Canje"]["valor"] = float(canje_data["valor"])
            resultados["Canje"]["fuente"] = "API Pública"
    except Exception as e:
        print(f"Error al obtener dólar canje: {str(e)}")
    
    # 4. Si aún falta MEP o CCL, intentar desde yfinance
    if not resultados["MEP"]["valor"] or not resultados["CCL"]["valor"]:
        try:
            bonos_data = obtener_bonos_yfinance()
            
            # Calcular MEP desde AL30 si está disponible
            if not resultados["MEP"]["valor"] and "AL30" in bonos_data:
                al30_data = bonos_data["AL30"]
                if al30_data.get("dolar_implicito"):
                    resultados["MEP"]["valor"] = round(al30_data["dolar_implicito"], 2)
                    resultados["MEP"]["fuente"] = "Yahoo Finance (AL30)"
            
            # Calcular CCL desde GD30 si está disponible
            if not resultados["CCL"]["valor"] and "GD30" in bonos_data:
                gd30_data = bonos_data["GD30"]
                if gd30_data.get("dolar_implicito"):
                    resultados["CCL"]["valor"] = round(gd30_data["dolar_implicito"], 2)
                    resultados["CCL"]["fuente"] = "Yahoo Finance (GD30)"
        except Exception as e:
            print(f"Error con yfinance: {str(e)}")
    
    return resultados

def obtener_resumen_rueda():
    """
    Obtiene y resume datos reales del mercado usando la API de IOL y scraping del BCRA.
    Incluye reservas, dólar mayorista, inflación, tasas, etc.
    """
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        # Incluso sin autenticación, podemos obtener algunos datos públicos
        try:
            variables_bcra = obtener_variables_bcra()
            reservas = obtener_reservas_bcra()
            dolares_financieros = obtener_dolares_financieros_completo()
            
            return {
                "reservas": reservas,
                "dolar_mayorista": {
                    "valor": variables_bcra.get("dolar_mayorista", {}).get("valor", "No disponible"),
                    "variacion": None
                },
                "volumen_operado": "Requiere autenticación IOL",
                "dolares_financieros": {
                    "MEP": dolares_financieros["MEP"],
                    "CCL": dolares_financieros["CCL"],
                    "Canje": dolares_financieros["Canje"],
                    "Blue": dolares_financieros["Blue"]
                },
                "merval": {"valor": "Requiere autenticación", "bajas": [], "subas": []},
                "deuda_soberana": {
                    "AL30D": "Requiere autenticación",
                    "GD35D": "Requiere autenticación", 
                    "GD38D": "Requiere autenticación"
                },
                "riesgo_pais": {"valor": "No disponible por API pública", "delta": None},
                "bonos_cer": {
                    "corto_plazo": [f"CER: {variables_bcra.get('cer', {}).get('valor', 'No disponible')}"],
                    "largo_plazo": ["Requiere autenticación IOL"]
                },
                "letras": ["Requiere autenticación IOL"],
                "dolar_linked": {
                    "futuros": "Requiere autenticación IOL",
                    "bonos": ["Requiere autenticación IOL"]
                },
                "caucion": {"plazo": "Requiere autenticación", "tasa": "Requiere autenticación"}
            }
        except Exception as e:
            st.warning(f"Error al obtener datos públicos: {str(e)}")
            return {
                "reservas": {"titulo": "Error", "valor": "Error al cargar", "delta": None},
                "dolar_mayorista": {"valor": "Error", "variacion": None},
                "volumen_operado": "Error",
                "dolares_financieros": {
                    "MEP": {"valor": "Error", "variacion": None, "fuente": None},
                    "CCL": {"valor": "Error", "variacion": None, "fuente": None},
                    "Canje": {"valor": "Error", "variacion": None, "fuente": None}
                },
                "merval": {"valor": "Error", "bajas": ["Error"], "subas": ["Error"]},
                "deuda_soberana": {"AL30D": "Error", "GD35D": "Error", "GD38D": "Error"},
                "riesgo_pais": {"valor": "Error", "delta": None},
                "bonos_cer": {"corto_plazo": ["Error"], "largo_plazo": ["Error"]},
                "letras": ["Error"],
                "dolar_linked": {"futuros": "Error", "bonos": ["Error"]},
                "caucion": {"plazo": "Error", "tasa": "Error"}
            }
    
    token_acceso = st.session_state.token_acceso

    try:
        # Obtener datos reales del BCRA primero
        variables_bcra = obtener_variables_bcra()
        
        # Reservas BCRA reales
        reservas = obtener_reservas_bcra()

        # Obtener dólares financieros usando métodos mejorados de IOL
        dolares_financieros = obtener_dolares_financieros_completo(token_acceso)

        # Datos reales de instrumentos principales desde IOL
        gd30 = obtener_cotizacion_detalle(token_acceso, 'GD30', 'BCBA')
        al30 = obtener_cotizacion_detalle(token_acceso, 'AL30', 'BCBA')
        gd35 = obtener_cotizacion_detalle(token_acceso, 'GD35', 'BCBA')
        gd38 = obtener_cotizacion_detalle(token_acceso, 'GD38', 'BCBA')
        merval = obtener_cotizacion_detalle(token_acceso, 'MERVAL', 'BCBA')
        dolar_mayorista_iol = obtener_cotizacion_detalle(token_acceso, 'DOLAR', 'BCBA')

        # Extraer datos del BCRA con mejor formato
        dolar_mayorista_bcra = variables_bcra.get("dolar_mayorista", {}).get("valor", None)
        dolar_minorista_bcra = variables_bcra.get("dolar_minorista", {}).get("valor", None)
        inflacion_mensual = variables_bcra.get("inflacion_mensual", {}).get("valor", None)
        inflacion_interanual = variables_bcra.get("inflacion_interanual", {}).get("valor", None)
        tasa_monetaria_na = variables_bcra.get("tasa_monetaria_na", {}).get("valor", None)
        tasa_monetaria_ea = variables_bcra.get("tasa_monetaria_ea", {}).get("valor", None)
        cer = variables_bcra.get("cer", {}).get("valor", None)
        base_monetaria = variables_bcra.get("base_monetaria", {}).get("valor", None)
        
        # Formatear el dólar mayorista del BCRA
        dolar_mayorista_valor = None
        if dolar_mayorista_bcra:
            try:
                dolar_mayorista_valor = float(dolar_mayorista_bcra.replace(".", "").replace(",", "."))
            except:
                dolar_mayorista_valor = dolar_mayorista_bcra

        # Los dólares financieros ya vienen calculados con los métodos mejorados
        # No necesitamos el cálculo manual anterior

        # Caución (real desde IOL)
        cauciones = obtener_tasas_caucion_iol(token_acceso)
        if cauciones:
            # Tomar el plazo más operado (mayor volumen o el de 7 días si existe)
            caucion_7d = next((c for c in cauciones if c.get("plazo") == 7), None)
            caucion_principal = caucion_7d if caucion_7d else (cauciones[0] if cauciones else None)
            tasa_caucion = caucion_principal["tasa"] if caucion_principal else "No disponible"
            plazo_caucion = f'{caucion_principal["plazo"]} días' if caucion_principal else "No disponible"
            # Para el gráfico, armar listas reales
            plazos_caucion = [c["plazo"] for c in cauciones if c.get("plazo") is not None]
            tasas_caucion = [c["tasa"] for c in cauciones if c.get("tasa") is not None]
        else:
            tasa_caucion = "No disponible"
            plazo_caucion = "No disponible"
            plazos_caucion = []
            tasas_caucion = []

        # Volumen operado del Merval
        volumen_operado = "No disponible"
        if merval and merval.get('volumenNominal'):
            try:
                volumen_millones = merval['volumenNominal'] / 1e6
                volumen_operado = f"USD {volumen_millones:.1f}M"
            except:
                volumen_operado = f"USD {merval['volumenNominal']}"
        # Resumen de bajas y subas del MERVAL (no disponible por API pública)
        bajas = ["Datos no disponibles por API pública"]
        subas = ["Datos no disponibles por API pública"]

        return {
            "reservas": reservas,
            "dolar_mayorista": {
                # Prioriza el valor del BCRA, que es más oficial
                "valor": dolar_mayorista_valor if dolar_mayorista_valor else (dolar_mayorista_iol["ultimoPrecio"] if dolar_mayorista_iol and dolar_mayorista_iol["ultimoPrecio"] else "No disponible"),
                "variacion": dolar_mayorista_iol["variacion"] if dolar_mayorista_iol else None
            },
            "dolar_minorista": {
                "valor": dolar_minorista_bcra,
                "fecha": variables_bcra.get("dolar_minorista", {}).get("fecha", None)
            },
            "volumen_operado": volumen_operado,
            "dolares_financieros": dolares_financieros,
            "merval": {
                "valor": merval["variacion"] if merval else None,
                "bajas": bajas,
                "subas": subas
            },
            "deuda_soberana": {
                "AL30D": al30["variacion"] if al30 else None,
                "GD35D": gd35["variacion"] if gd35 else None,
                "GD38D": gd38["variacion"] if gd38 else None
            },
            "riesgo_pais": {
                "valor": "No disponible por API pública",
                "delta": None
            },
            "bonos_cer": {
                "corto_plazo": [f"CER: {cer}" if cer else "Datos del BCRA"],
                "largo_plazo": ["Consultar IOL para datos detallados"]
            },
            "letras": ["Consultar IOL para datos actualizados"],
            "dolar_linked": {
                "futuros": "Consultar IOL para cotizaciones",
                "bonos": ["Consultar IOL para datos específicos"]
            },
            "caucion": {
                "plazo": plazo_caucion,
                "tasa": tasa_caucion,
                "plazos_lista": plazos_caucion,
                "tasas_lista": tasas_caucion
            },
            "inflacion": {
                "mensual": inflacion_mensual,
                "interanual": inflacion_interanual
            },
            "tasas_bcra": {
                "politica_monetaria_na": tasa_monetaria_na,
                "politica_monetaria_ea": tasa_monetaria_ea
            },
            "variables_monetarias": {
                "base_monetaria": base_monetaria,
                "cer": cer,
                "uva": variables_bcra.get("uva", {}).get("valor", None),
                "uvi": variables_bcra.get("uvi", {}).get("valor", None),
                "icl": variables_bcra.get("icl", {}).get("valor", None)
            }
        }
    except Exception as e:
        st.error(f"Error al obtener datos de mercado: {str(e)}")
        # Retornar estructura con datos del BCRA si falla IOL
        try:
            variables_bcra = obtener_variables_bcra()
            reservas_fallback = obtener_reservas_bcra()
            return {
                "reservas": reservas_fallback,
                "dolar_mayorista": {
                    "valor": variables_bcra.get("dolar_mayorista", {}).get("valor", "Error al cargar"),
                    "variacion": None
                },
                "volumen_operado": "Error de conexión IOL",
                "dolares_financieros": {
                    "MEP": {"valor": "Sin datos IOL", "variacion": None},
                    "CCL": {"valor": "Sin datos IOL", "variacion": None},
                    "Canje": {"valor": 0, "variacion": None}
                },
                "merval": {"valor": "Sin datos IOL", "bajas": ["Error de conexión"], "subas": ["Error de conexión"]},
                "deuda_soberana": {"AL30D": "Sin datos", "GD35D": "Sin datos", "GD38D": "Sin datos"},
                "riesgo_pais": {"valor": "Sin datos", "delta": None},
                "bonos_cer": {"corto_plazo": [f"CER BCRA: {variables_bcra.get('cer', {}).get('valor', 'No disponible')}"], "largo_plazo": ["Error de conexión"]},
                "letras": ["Error de conexión"],
                "dolar_linked": {"futuros": "Error de conexión", "bonos": ["Error de conexión"]},
                "caucion": {"plazo": "Error de conexión", "tasa": "Sin datos"}
            }
        except:
            # Fallback completo en caso de error total
            return {
                "reservas": {"titulo": "Error", "valor": "Error al cargar", "delta": None},
                "dolar_mayorista": {"valor": "Error", "variacion": None},
                "volumen_operado": "Error",
                "dolares_financieros": {
                    "MEP": {"valor": "Error", "variacion": None},
                    "CCL": {"valor": "Error", "variacion": None},
                    "Canje": {"valor": "Error", "variacion": None}
                },
                "merval": {"valor": "Error", "bajas": ["Error"], "subas": ["Error"]},
                "deuda_soberana": {"AL30D": "Error", "GD35D": "Error", "GD38D": "Error"},
                "riesgo_pais": {"valor": "Error", "delta": None},
                "bonos_cer": {"corto_plazo": ["Error"], "largo_plazo": ["Error"]},
                "letras": ["Error"],
                "dolar_linked": {"futuros": "Error", "bonos": ["Error"]},
                "caucion": {"plazo": "Error", "tasa": "Error"}
            }

def mostrar_resumen_rueda():
    """Muestra el resumen de la rueda del día con validación de datos reales."""
    st.markdown("## 🔔 Resumen de la Rueda del Día")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    resumen = obtener_resumen_rueda()
    
    # Utilidad para mostrar "No disponible" si el valor es 0, None o vacío
    def mostrar_valor(valor, formato="${:,.2f}", nd="No disponible"):
        if valor is None or (isinstance(valor, (int, float)) and valor == 0):
            return nd
        if isinstance(valor, (int, float)):
            return formato.format(valor)
        return valor

    # Sección 1: Reservas y Dólar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=resumen["reservas"]["titulo"],
            value=mostrar_valor(resumen["reservas"]["valor"], formato="{}", nd="No disponible"),
            delta=resumen["reservas"]["delta"]
        )
    with col2:
        st.metric(
            label="Dólar Mayorista (A3500)",
            value=mostrar_valor(resumen['dolar_mayorista']['valor']),
            delta=f"{resumen['dolar_mayorista']['variacion']}%" if resumen['dolar_mayorista']['variacion'] not in [None, 0] else None
        )
    with col3:
        st.metric(
            label="Volumen Operado A3",
            value=mostrar_valor(resumen["volumen_operado"], formato="{}", nd="No disponible"),
            delta=None
        )
    st.divider()
    
    # Sección 2: Dólares Financieros (mejorada con indicadores de precisión)
    st.subheader("💸 Dólares Financieros")
    cols = st.columns(4)
    
    dolares = resumen['dolares_financieros']
    
    with cols[0]:
        mep_valor = mostrar_valor(dolares['MEP']['valor'])
        mep_delta = f"{dolares['MEP']['variacion']}%" if dolares['MEP']['variacion'] not in [None, 0] else None
        st.metric("MEP", mep_valor, mep_delta)
        if dolares['MEP']['fuente']:
            # Indicador de calidad de la fuente
            if "IOL MEP" in dolares['MEP']['fuente']:
                st.caption(f"🎯 {dolares['MEP']['fuente']} (Preciso)")
            elif "IOL" in dolares['MEP']['fuente']:
                st.caption(f"📊 {dolares['MEP']['fuente']} (Estimado)")
            else:
                st.caption(f"📡 {dolares['MEP']['fuente']}")
    
    with cols[1]:
        ccl_valor = mostrar_valor(dolares['CCL']['valor'])
        ccl_delta = f"{dolares['CCL']['variacion']}%" if dolares['CCL']['variacion'] not in [None, 0] else None
        st.metric("CCL", ccl_valor, ccl_delta)
        if dolares['CCL']['fuente']:
            if "IOL CCL" in dolares['CCL']['fuente']:
                st.caption(f"🎯 {dolares['CCL']['fuente']} (Preciso)")
            elif "IOL" in dolares['CCL']['fuente']:
                st.caption(f"📊 {dolares['CCL']['fuente']} (Estimado)")
            else:
                st.caption(f"📡 {dolares['CCL']['fuente']}")
    
    with cols[2]:
        canje_valor = mostrar_valor(dolares['Canje']['valor'])
        st.metric("Canje/Tarjeta", canje_valor, None)
        if dolares['Canje']['fuente']:
            st.caption(f"📡 {dolares['Canje']['fuente']}")
    
    with cols[3]:
        blue_valor = mostrar_valor(dolares.get('Blue', {}).get('valor'))
        st.metric("Blue", blue_valor, None)
        if dolares.get('Blue', {}).get('fuente'):
            st.caption(f"📡 {dolares['Blue']['fuente']}")
    
    st.caption("🔹 Prioridad: IOL API específico → IOL estimado → APIs públicas → Yahoo Finance")
    st.divider()
    
    # Sección 3: Merval
    st.subheader(f"📉 S&P Merval: {mostrar_valor(resumen['merval']['valor'], formato='{}%', nd='No disponible')}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Principales bajas:**")
        for baja in resumen["merval"]["bajas"]:
            st.markdown(f"- {baja}")
    with col2:
        st.markdown("**Principales subas:**")
        for suba in resumen["merval"]["subas"]:
            st.markdown(f"- {suba}")
    st.divider()
    
    # Sección 4: Deuda Soberana
    st.subheader("💵 Deuda Soberana en USD (Hard Dollar)")
    cols = st.columns(4)
    with cols[0]:
        st.metric("AL30D", mostrar_valor(resumen['deuda_soberana']['AL30D'], formato="{}%", nd="No disponible"))
    with cols[1]:
        st.metric("GD35D", mostrar_valor(resumen['deuda_soberana']['GD35D'], formato="{}%", nd="No disponible"))
    with cols[2]:
        st.metric("GD38D", mostrar_valor(resumen['deuda_soberana']['GD38D'], formato="{}%", nd="No disponible"))
    with cols[3]:
        st.metric("Riesgo País", mostrar_valor(resumen['riesgo_pais']['valor'], formato="{}", nd="No disponible"), 
                 f"{resumen['riesgo_pais']['delta']} puntos" if resumen['riesgo_pais']['delta'] else None)
    st.divider()
    
    # Sección 5: Bonos CER
    st.subheader("📊 Bonos CER")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Corto plazo en alza:**")
        for bono in resumen["bonos_cer"]["corto_plazo"]:
            st.markdown(f"- {bono}")
    with col2:
        st.markdown("**Largo plazo en baja:**")
        for bono in resumen["bonos_cer"]["largo_plazo"]:
            st.markdown(f"- {bono}")
    st.divider()
    
    # Sección 6: Letras y Dólar Linked
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Letras")
        for letra in resumen["letras"]:
            st.markdown(f"- {letra}")
    with col2:
        st.subheader("🔄 Dólar Linked")
        st.markdown(f"▫️ Futuros suben entre {mostrar_valor(resumen['dolar_linked']['futuros'], formato='{}', nd='No disponible')}")
        st.markdown("▫️ Bonos:")
        for bono in resumen["dolar_linked"]["bonos"]:
            st.markdown(f"  - {bono}")
    st.divider()
    
    # Sección 7: Caución
    st.subheader(f"📌 Caución a {mostrar_valor(resumen['caucion']['plazo'], formato='{}', nd='No disponible')}: {mostrar_valor(resumen['caucion']['tasa'], formato='{}%', nd='No disponible')}")
    
    # Gráfico de tasas de caución (reales si existen)
    plazos = resumen["caucion"].get("plazos_lista", [])
    tasas = resumen["caucion"].get("tasas_lista", [])
    if plazos and tasas and len(plazos) == len(tasas):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plazos, 
            y=tasas,
            mode='lines+markers',
            name='Tasas',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=10, color='#2E7D32')
        ))
        fig.update_layout(
            title='Curva de Tasas de Caución',
            xaxis_title='Plazo (días)',
            yaxis_title='Tasa (%)',
            template='plotly_dark',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        # fallback simulado si no hay datos reales
        plazos = [1, 7, 14, 30, 60]
        tasas = [25.5, 28.8, 27.2, 26.5, 25.8]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plazos, 
            y=tasas,
            mode='lines+markers',
            name='Tasas',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=10, color='#2E7D32')
        ))
        fig.update_layout(
            title='Curva de Tasas de Caución',
            xaxis_title='Plazo (días)',
            yaxis_title='Tasa (%)',
            template='plotly_dark',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

# ... (código existente previo a la función main)

def obtener_tokens(usuario, contraseña):
    """
    Realiza la autenticación contra la API de IOL y devuelve el token de acceso y refresh token.
    """
    try:
        url = "https://api.invertironline.com/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "username": usuario,
            "password": contraseña,
            "grant_type": "password"
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        tokens = response.json()
        return tokens.get("access_token"), tokens.get("refresh_token")
    except Exception as e:
        print(f"Error al obtener tokens: {str(e)}")
        return None, None

def obtener_lista_clientes(token_acceso):
    """
    Obtiene la lista de clientes asociados al usuario autenticado en IOL.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        url = "https://api.invertironline.com/api/v2/estadocuenta"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Si la API devuelve una lista de cuentas, adaptamos el formato
        if isinstance(data, list):
            return data
        # Si devuelve un solo cliente, lo envolvemos en una lista
        elif isinstance(data, dict):
            return [data]
        else:
            return []
    except Exception as e:
        print(f"Error al obtener lista de clientes: {str(e)}")
        return []

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
                    label_visibility="collapsed",
                    key="sidebar_cliente_selector"
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", 
                 "👨‍💼 Panel del Asesor", "🔔 Resumen de la Rueda"),
                index=0,
                key="main_navigation_radio"
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
                
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
            
            elif opcion == "🔔 Resumen de la Rueda":
                mostrar_resumen_rueda()
        else:
            st.info("👆 Ingrese sus credenciales para comenzar")
            
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

if __name__ == "__main__":
    main()
