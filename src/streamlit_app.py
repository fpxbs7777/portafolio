import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import requests
from bs4 import BeautifulSoup
import urllib3
import yfinance as yf
import pandas as pd
import json
import time
import re
from typing import Dict, Optional
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DolarScraper:
    def __init__(self):
        self.url = "https://dolarhoy.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.last_update = None
        self.rates = {}

    def fetch_data(self):
        try:
            print("\n🔍 Obteniendo datos desde dolarhoy.com...")
            session = requests.Session()
            session.headers.update(self.headers)
            
            # Add cache buster to prevent cached responses
            url = f"{self.url}?t={int(time.time())}"
            
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            # Verify we got the actual content and not an error page
            if 'dolar' not in response.text.lower():
                raise Exception("No se pudo obtener la página de cotizaciones")
                
            return response.text
            
        except requests.RequestException as e:
            print(f"\n❌ Error al conectar con dolarhoy.com: {e}")
            print("Intente verificar su conexión a internet o intente nuevamente más tarde.")
            return None
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}")
            return None

    def clean_text(self, text: str) -> str:
        """Clean and normalize text by removing extra whitespace and newlines."""
        if not text:
            return ''
        return ' '.join(text.strip().split())

    def parse_data(self, html_content: str) -> Optional[Dict]:
        """Parse the HTML content to extract exchange rates."""
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')
        rates = {}
        
        # Find all currency containers
        containers = soup.find_all('div', class_='tile is-child')
        
        for container in containers:
            try:
                # Extract title
                title_elem = container.find('a', class_='titleText')
                if not title_elem:
                    title_elem = container.find('div', class_='title')
                    if title_elem:
                        title_elem = title_elem.find('a', class_='titleText')
                
                if not title_elem:
                    continue
                    
                title = self.clean_text(title_elem.text)
                if not any(d in title for d in ['Dólar', 'Contado']):
                    continue
                
                values = {}
                
                # Extract buy price
                buy_elem = container.find('div', class_='compra')
                if buy_elem:
                    buy_val = buy_elem.find('div', class_='val')
                    if buy_val:
                        values['compra'] = self.clean_text(buy_val.text)
                
                # Extract sell price
                sell_elem = container.find('div', class_='venta')
                if sell_elem:
                    sell_val = sell_elem.find('div', class_='val')
                    if sell_val:
                        values['venta'] = self.clean_text(sell_val.text)
                    else:
                        # Some elements might have the value directly in the venta div
                        sell_text = sell_elem.get_text()
                        if '$' in sell_text:
                            values['venta'] = self.clean_text(sell_text)
                
                # Extract variation - handle both direct text and nested elements
                var_elem = container.find('div', class_='var-porcentaje')
                if var_elem:
                    # First try to find a direct text node with percentage
                    var_text = ''.join([str(t) for t in var_elem.contents if isinstance(t, str)]).strip()
                    # Clean any XML/HTML artifacts
                    var_text = re.sub(r'<[^>]+>', '', var_text)  # Remove any HTML tags
                    var_text = re.sub(r'&[^;]+;', '', var_text)  # Remove HTML entities
                    var_text = var_text.strip()
                    
                    # If we found a percentage, use it
                    if '%' in var_text:
                        values['variacion'] = var_text
                    # Otherwise try to find a number with percentage
                    else:
                        match = re.search(r'([-+]?\d*\.?\d+%?)', var_text)
                        if match:
                            values['variacion'] = match.group(1)
                
                if values:
                    rates[title] = values
                
                # Update timestamp
                update_elem = container.find('div', class_='tile update')
                if not update_elem:
                    update_elem = container.find('div', class_='update')
                if update_elem:
                    self.last_update = self.clean_text(
                        update_elem.text.replace('Actualizado por última vez:', '')
                    )
                
            except Exception as e:
                print(f"Error al procesar elemento: {str(e)}")
                continue
        
        # If we didn't find rates in the main containers, try alternative approach
        if not rates:
            return self._parse_alternative_structure(soup)
        
        self.rates = rates
        return rates
    
    def _parse_alternative_structure(self, soup) -> Dict:
        """Alternative parsing method if the main method fails."""
        rates = {}
        
        # Look for all currency blocks
        currency_blocks = soup.find_all('div', class_='tile is-child')
        
        for block in currency_blocks:
            try:
                # Get the title
                title_elem = block.find('a', class_='titleText')
                if not title_elem:
                    title_elem = block.find('div', class_='title')
                    if title_elem:
                        title_elem = title_elem.find('a')
                
                if not title_elem:
                    continue
                
                title = self.clean_text(title_elem.text)
                if not any(d in title for d in ['Dólar', 'Contado']):
                    continue
                
                values = {}
                
                # Extract prices
                for price_type in ['compra', 'venta']:
                    price_div = block.find('div', class_=price_type)
                    if price_div:
                        val = price_div.find('div', class_='val')
                        if val:
                            values[price_type] = self.clean_text(val.text)
                
                # Extract variation with better handling
                var_div = block.find('div', class_='var-porcentaje')
                if var_div:
                    # Get all text content, including from nested elements
                    var_text = ''.join([str(t) for t in var_div.contents if isinstance(t, str)])
                    # Clean up the text
                    var_text = re.sub(r'<[^>]+>', '', var_text)  # Remove any HTML tags
                    var_text = re.sub(r'&[^;]+;', '', var_text)  # Remove HTML entities
                    var_text = var_text.strip()
                    
                    # Find percentage value
                    match = re.search(r'([-+]?\d*\.?\d+%?)', var_text)
                    if match:
                        values['variacion'] = match.group(1)
                    elif '%' in var_text:
                        values['variacion'] = var_text
                
                if values:
                    rates[title] = values
                
                # Update timestamp if found
                update_div = block.find('div', class_='tile update')
                if update_div:
                    self.last_update = self.clean_text(
                        update_div.text.replace('Actualizado por última vez:', '')
                    )
                
            except Exception as e:
                print(f"Error en método alternativo: {str(e)}")
                continue
        
        self.rates = rates
        return rates

    def get_rates(self):
        html_content = self.fetch_data()
        if html_content:
            return self.parse_data(html_content)
        return None

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the scraped rates to a pandas DataFrame."""
        if not self.rates:
            self.get_rates()
        
        data = []
        for currency, values in self.rates.items():
            row = {'Moneda': currency}
            
            # Ensure all expected columns exist
            for col in ['compra', 'venta', 'variacion']:
                row[col] = values.get(col, 'N/A')
            
            # Clean up the values
            for key in ['compra', 'venta']:
                if key in row and row[key] != 'N/A':
                    # Remove currency symbols and clean up
                    row[key] = row[key].replace('$', '').replace(',', '.').strip()
                    # Try to convert to float if it's a valid number
                    try:
                        row[key] = float(row[key])
                    except (ValueError, TypeError):
                        pass
            
            data.append(row)
        
        # Create DataFrame with consistent column order
        columns = ['Moneda', 'compra', 'venta', 'variacion']
        df = pd.DataFrame(data, columns=columns)
        
        return df

def obtener_dolares_dolarhoy():
    """
    Obtiene cotizaciones de dólar desde dolarhoy.com usando scraping.
    """
    try:
        scraper = DolarScraper()
        rates = scraper.get_rates()
        
        if rates:
            # Normalizar los nombres para compatibilidad
            resultados = {}
            
            for nombre, datos in rates.items():
                # Extraer valores y limpiarlos
                compra = datos.get('compra', 'N/A')
                venta = datos.get('venta', 'N/A')
                variacion = datos.get('variacion', 'N/A')
                
                # Limpiar valores numéricos
                try:
                    if compra != 'N/A':
                        compra = float(str(compra).replace('$', '').replace(',', '.').strip())
                    if venta != 'N/A':
                        venta = float(str(venta).replace('$', '').replace(',', '.').strip())
                except (ValueError, TypeError):
                    pass
                
                # Mapear a nombres estándar
                key = None
                nombre_lower = nombre.lower()
                
                if 'oficial' in nombre_lower:
                    key = 'oficial'
                elif 'blue' in nombre_lower or 'paralelo' in nombre_lower:
                    key = 'blue'
                elif 'mep' in nombre_lower or 'bolsa' in nombre_lower:
                    key = 'mep'
                elif 'contado con liquidación' in nombre_lower or 'ccl' in nombre_lower:
                    key = 'ccl'
                elif 'mayorista' in nombre_lower:
                    key = 'mayorista'
                elif 'tarjeta' in nombre_lower or 'turista' in nombre_lower:
                    key = 'tarjeta'
                
                if key:
                    resultados[key] = {
                        'compra': compra,
                        'venta': venta,
                        'variacion': variacion,
                        'fechaActualizacion': scraper.last_update
                    }
            
            return resultados
            
    except Exception as e:
        print(f"Error al obtener datos de dolarhoy.com: {str(e)}")
        return {}
    
    return {}

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
        
        # Debug: mostrar respuesta
        print(f"MEP Response para {simbolo}: {mep_valor}")
        
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
        # Pares de acciones argentinas y sus ADRs con ratios correctos
        pares_ccl = [
            {"local": "GGAL", "adr": "GGAL", "ratio": 1},     # Galicia 1:1
            {"local": "YPF", "adr": "YPF", "ratio": 1},       # YPF 1:1
            {"local": "PAM", "adr": "PAM", "ratio": 0.04},    # Pampa 25:1 (1/25)
            {"local": "BMA", "adr": "BMA", "ratio": 0.1},     # Banco Macro 10:1
            {"local": "SUPV", "adr": "SUPV", "ratio": 0.2}   # Supervielle 5:1
        ]
        
        ccl_valores = []
        
        for par in pares_ccl:
            try:
                # Obtener cotización local (en pesos) desde BCBA
                accion_local = obtener_cotizacion_detalle(token_acceso, par["local"], 'BCBA')
                
                # Para ADRs, intentar primero NYSE, luego NASDAQ
                adr_data = None
                for mercado in ['NYSE', 'NASDAQ']:
                    adr_data = obtener_cotizacion_detalle(token_acceso, par["adr"], mercado)
                    if adr_data and adr_data.get("ultimoPrecio"):
                        break
                
                if accion_local and adr_data and accion_local.get("ultimoPrecio") and adr_data.get("ultimoPrecio"):
                    precio_local = accion_local["ultimoPrecio"]
                    precio_adr_usd = adr_data["ultimoPrecio"]
                    ratio = par["ratio"]
                    
                    # Calcular CCL implícito: precio_local / (precio_adr * ratio)
                    ccl_implicito = precio_local / (precio_adr_usd / ratio)
                    
                    print(f"CCL {par['local']}: Local=${precio_local}, ADR=${precio_adr_usd}, Ratio={ratio}, CCL=${ccl_implicito:.2f}")
                    
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
            
            print(f"CCL promedio calculado: ${ccl_promedio:.2f} desde {len(ccl_valores)} instrumentos")
            
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

def calcular_mep_desde_bonos_iol(token_acceso):
    """
    Calcula MEP usando bonos soberanos desde IOL (método alternativo más preciso).
    """
    try:
        # Bonos para calcular MEP
        bonos_mep = [
            {"simbolo": "AL30", "mercado_local": "BCBA", "mercado_ext": "NYSE"},
            {"simbolo": "AL35", "mercado_local": "BCBA", "mercado_ext": "NYSE"}, 
            {"simbolo": "GD30", "mercado_local": "BCBA", "mercado_ext": "NYSE"}
        ]
        
        mep_valores = []
        
        for bono in bonos_mep:
            try:
                # Obtener precio en pesos (mercado local)
                bono_local = obtener_cotizacion_detalle(token_acceso, bono["simbolo"], bono["mercado_local"])
                
                # Obtener precio en USD (mercado externo)
                bono_ext = obtener_cotizacion_detalle(token_acceso, bono["simbolo"], bono["mercado_ext"])
                
                if bono_local and bono_ext and bono_local.get("ultimoPrecio") and bono_ext.get("ultimoPrecio"):
                    precio_local = bono_local["ultimoPrecio"]
                    precio_usd = bono_ext["ultimoPrecio"]
                    
                    # MEP = precio_local / precio_usd (asumiendo paridad 1:1 en bonos)
                    mep_valor = precio_local / precio_usd
                    
                    print(f"MEP {bono['simbolo']}: Local=${precio_local}, USD=${precio_usd}, MEP=${mep_valor:.2f}")
                    
                    mep_valores.append({
                        "valor": mep_valor,
                        "simbolo": bono["simbolo"],
                        "precio_local": precio_local,
                        "precio_usd": precio_usd
                    })
                    
            except Exception as e:
                print(f"Error al procesar bono {bono['simbolo']}: {str(e)}")
                continue
        
        if mep_valores:
            # Promediar los valores MEP
            mep_promedio = sum(item["valor"] for item in mep_valores) / len(mep_valores)
            
            print(f"MEP promedio calculado: ${mep_promedio:.2f} desde {len(mep_valores)} bonos")
            
            return {
                "valor": round(mep_promedio, 2),
                "cantidad_instrumentos": len(mep_valores),
                "detalle": mep_valores,
                "fuente": "IOL Bonos (Calculado)"
            }
        
        return None
        
    except Exception as e:
        print(f"Error al calcular MEP desde bonos: {str(e)}")
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
            if mep_data and mep_data.get("valor") and mep_data["valor"] > 0:
                resultados["MEP"]["valor"] = mep_data["valor"]
                resultados["MEP"]["fuente"] = f"IOL MEP ({bono})"
                print(f"MEP obtenido exitosamente: ${mep_data['valor']}")
                break
                
    except Exception as e:
        print(f"Error al obtener MEP directo: {str(e)}")
    
    # 2. Si no se obtuvo MEP del endpoint, calcular desde bonos
    if not resultados["MEP"]["valor"]:
        try:
            mep_bonos = calcular_mep_desde_bonos_iol(token_acceso)
            if mep_bonos and mep_bonos.get("valor"):
                resultados["MEP"]["valor"] = mep_bonos["valor"]
                resultados["MEP"]["fuente"] = f"IOL Bonos ({mep_bonos['cantidad_instrumentos']} instrumentos)"
        except Exception as e:
            print(f"Error al calcular MEP desde bonos: {str(e)}")
    
    # 3. Calcular CCL desde acciones/ADRs
    try:
        ccl_data = obtener_ccl_desde_acciones_iol(token_acceso)
        if ccl_data and ccl_data.get("valor"):
            resultados["CCL"]["valor"] = ccl_data["valor"]
            resultados["CCL"]["fuente"] = f"IOL CCL ({ccl_data['cantidad_instrumentos']} instrumentos)"
            
    except Exception as e:
        print(f"Error al calcular CCL: {str(e)}")
    
    # 4. Si no obtuvimos MEP, usar método estimativo simple
    if not resultados["MEP"]["valor"]:
        try:
            al30 = obtener_cotizacion_detalle(token_acceso, 'AL30', 'BCBA')
            if al30 and al30.get("ultimoPrecio"):
                # Usar precio AL30 como referencia (ajustar según corresponda)
                precio_al30 = al30["ultimoPrecio"]
                
                # Si el precio es muy alto, dividir por 100 (podría estar en centavos)
                if precio_al30 > 2000:
                    mep_estimado = precio_al30 / 100
                elif precio_al30 > 200:
                    mep_estimado = precio_al30 / 10
                else:
                    mep_estimado = precio_al30
                
                resultados["MEP"]["valor"] = round(mep_estimado, 2)
                resultados["MEP"]["fuente"] = "IOL AL30 (estimado)"
                
                # Calcular variación si tenemos apertura
                if al30.get("apertura"):
                    apertura = al30["apertura"]
                    if apertura > 2000:
                        apertura = apertura / 100
                    elif apertura > 200:
                        apertura = apertura / 10
                        
                    variacion = ((mep_estimado - apertura) / apertura) * 100
                    resultados["MEP"]["variacion"] = round(variacion, 2)
                    
        except Exception as e:
            print(f"Error al calcular MEP estimado: {str(e)}")
    
    # 5. Si no obtuvimos CCL, usar método estimativo con GD30
    if not resultados["CCL"]["valor"]:
        try:
            gd30 = obtener_cotizacion_detalle(token_acceso, 'GD30', 'BCBA')
            if gd30 and gd30.get("ultimoPrecio"):
                precio_gd30 = gd30["ultimoPrecio"]
                
                # Ajustar precio similar al MEP
                if precio_gd30 > 2000:
                    ccl_estimado = precio_gd30 / 100
                elif precio_gd30 > 200:
                    ccl_estimado = precio_gd30 / 10
                else:
                    ccl_estimado = precio_gd30
                
                resultados["CCL"]["valor"] = round(ccl_estimado, 2)
                resultados["CCL"]["fuente"] = "IOL GD30 (estimado)"
                
                # Calcular variación
                if gd30.get("apertura"):
                    apertura = gd30["apertura"]
                    if apertura > 2000:
                        apertura = apertura / 100
                    elif apertura > 200:
                        apertura = apertura / 10
                        
                    variacion = ((ccl_estimado - apertura) / apertura) * 100
                    resultados["CCL"]["variacion"] = round(variacion, 2)
                    
        except Exception as e:
            print(f"Error al calcular CCL estimado: {str(e)}")
    
    return resultados

def obtener_dolares_financieros_completo(token_acceso=None):
    """
    Obtiene cotizaciones de dólares financieros desde múltiples fuentes.
    Combina datos de IOL, APIs públicas, dolarhoy.com y yfinance.
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
    
    # 2. Intentar obtener desde dolarhoy.com
    try:
        cotizaciones_dolarhoy = obtener_dolares_dolarhoy()
        if cotizaciones_dolarhoy:
            # Solo usar dolarhoy si no tenemos datos de IOL o como complemento
            if not resultados["MEP"]["valor"] and "mep" in cotizaciones_dolarhoy and cotizaciones_dolarhoy["mep"].get("venta"):
                resultados["MEP"]["valor"] = float(cotizaciones_dolarhoy["mep"]["venta"])
                resultados["MEP"]["fuente"] = "DolarHoy.com"
            
            if not resultados["CCL"]["valor"] and "ccl" in cotizaciones_dolarhoy and cotizaciones_dolarhoy["ccl"].get("venta"):
                resultados["CCL"]["valor"] = float(cotizaciones_dolarhoy["ccl"]["venta"])
                resultados["CCL"]["fuente"] = "DolarHoy.com"
            
            if "blue" in cotizaciones_dolarhoy and cotizaciones_dolarhoy["blue"].get("venta"):
                resultados["Blue"]["valor"] = float(cotizaciones_dolarhoy["blue"]["venta"])
                resultados["Blue"]["fuente"] = "DolarHoy.com"
            
            if not resultados["Canje"]["valor"] and "tarjeta" in cotizaciones_dolarhoy and cotizaciones_dolarhoy["tarjeta"].get("venta"):
                resultados["Canje"]["valor"] = float(cotizaciones_dolarhoy["tarjeta"]["venta"])
                resultados["Canje"]["fuente"] = "DolarHoy.com"
    except Exception as e:
        print(f"Error con dolarhoy.com: {str(e)}")
    
    # 3. Intentar obtener desde API pública (como fallback adicional)
    try:
        cotizaciones_api = obtener_dolar_api_publica()
        if cotizaciones_api:
            # Solo usar API pública si no tenemos datos de IOL o dolarhoy
            if not resultados["MEP"]["valor"] and "mep" in cotizaciones_api and cotizaciones_api["mep"].get("venta"):
                resultados["MEP"]["valor"] = float(cotizaciones_api["mep"]["venta"])
                resultados["MEP"]["fuente"] = "API Pública"
            
            if not resultados["CCL"]["valor"] and "ccl" in cotizaciones_api and cotizaciones_api["ccl"].get("venta"):
                resultados["CCL"]["valor"] = float(cotizaciones_api["ccl"]["venta"])
                resultados["CCL"]["fuente"] = "API Pública"
            
            if not resultados["Blue"]["valor"] and "blue" in cotizaciones_api and cotizaciones_api["blue"].get("venta"):
                resultados["Blue"]["valor"] = float(cotizaciones_api["blue"]["venta"])
                resultados["Blue"]["fuente"] = "API Pública"
    except Exception as e:
        print(f"Error con API pública: {str(e)}")
    
    # 4. Obtener dólar canje si aún no lo tenemos
    if not resultados["Canje"]["valor"]:
        try:
            canje_data = obtener_dolar_canje()
            if canje_data and canje_data.get("valor"):
                resultados["Canje"]["valor"] = float(canje_data["valor"])
                resultados["Canje"]["fuente"] = "API Pública (Calculado)"
        except Exception as e:
            print(f"Error al obtener dólar canje: {str(e)}")
    
    # 5. Si aún falta MEP o CCL, intentar desde yfinance
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

def mostrar_analisis_portafolio():
    """Función placeholder para análisis de portafolio"""
    st.subheader("📊 Análisis de Portafolio")
    st.info("Esta funcionalidad estará disponible próximamente. Requiere implementación completa de análisis de posiciones.")

def mostrar_tasas_caucion(token_acceso):
    """Función para mostrar tasas de caución"""
    st.subheader("💰 Tasas de Caución")
    
    try:
        cauciones = obtener_tasas_caucion_iol(token_acceso)
        
        if cauciones:
            st.success(f"✅ Se encontraron {len(cauciones)} tasas de caución")
            
            # Crear DataFrame para mostrar
            df_cauciones = pd.DataFrame(cauciones)
            
            # Mostrar tabla
            st.dataframe(df_cauciones, use_container_width=True)
            
            # Gráfico de tasas por plazo
            if len(cauciones) > 1:
                plazos = [c["plazo"] for c in cauciones if c.get("plazo")]
                tasas = [c["tasa"] for c in cauciones if c.get("tasa")]
                
                if plazos and tasas:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=plazos,
                        y=tasas,
                        mode='lines+markers',
                        name='Tasas de Caución',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=8)
                    ))
                    
                    fig.update_layout(
                        title='Curva de Tasas de Caución',
                        xaxis_title='Plazo (días)',
                        yaxis_title='Tasa (%)',
                        template='plotly_white',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron tasas de caución disponibles")
            
    except Exception as e:
        st.error(f"Error al obtener tasas de caución: {str(e)}")

def mostrar_movimientos_asesor():
    """Función placeholder para panel del asesor"""
    st.subheader("👨‍💼 Panel del Asesor")
    st.info("Esta funcionalidad estará disponible próximamente. Requiere implementación de análisis de movimientos y reportes.")

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
