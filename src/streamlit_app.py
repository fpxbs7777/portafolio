import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.optimize import minimize
import warnings
from typing import Dict, List, Optional, Tuple, Union
warnings.filterwarnings('ignore')

# Configuración de estilo para gráficos
try:
    plt.style.use('seaborn')
except OSError:
    plt.style.use('default')  # Fallback to default style if seaborn is not available
plt.rcParams['figure.figsize'] = [12, 6]

# Constantes para perfiles de inversor
PERFILES_INVERSOR = {
    'CONSERVADOR': {
        'nombre': 'Conservador',
        'descripcion': 'Prefiere bajo riesgo y estabilidad en sus inversiones.',
        'composicion': [
            {'tipo': 'Renta Fija', 'min': 70, 'max': 100},
            {'tipo': 'Renta Mixta', 'min': 0, 'max': 30},
            {'tipo': 'Renta Variable', 'min': 0, 'max': 10}
        ]
    },
    'MODERADO': {
        'nombre': 'Moderado',
        'descripcion': 'Busca equilibrio entre riesgo y retorno.',
        'composicion': [
            {'tipo': 'Renta Fija', 'min': 40, 'max': 70},
            {'tipo': 'Renta Mixta', 'min': 20, 'max': 50},
            {'tipo': 'Renta Variable', 'min': 10, 'max': 30}
        ]
    },
    'ARRIESGADO': {
        'nombre': 'Arriesgado',
        'descripcion': 'Buscador de altos retornos asumiendo mayor riesgo.',
        'composicion': [
            {'tipo': 'Renta Fija', 'min': 0, 'max': 30},
            {'tipo': 'Renta Mixta', 'min': 20, 'max': 50},
            {'tipo': 'Renta Variable', 'min': 40, 'max': 70}
        ]
    }
}

def obtener_tokens(username, password):
    token_url = 'https://api.invertironline.com/token'
    payload = {
        'username': username,
        'password': password,
        'grant_type': 'password'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        print(f'Error en la solicitud: {response.status_code}')
        print(response.text)
        return None, None

def refrescar_token(refresh_token):
    token_url = 'https://api.invertironline.com/token'
    payload = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        print(f'Error en la solicitud: {response.status_code}')
        print(response.text)
        return None, None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Obtiene series históricas para diferentes tipos de activos con manejo mejorado de errores,
    reintentos automáticos y soporte para diferentes formatos de fechas.
    
    Args:
        token_portador (str): Token de autenticación Bearer
        mercado (str): Tipo de mercado (ej: 'acciones', 'bonos', 'fci', 'opciones')
        simbolo (str): Símbolo del activo
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        ajustada (str): 'ajustada' o 'noajustada' para precios ajustados
        
    Returns:
        pd.Series: Serie temporal con los precios históricos o None en caso de error
    """
    max_retries = 3
    
    # Validar fechas
    try:
        fecha_desde_dt = parse_datetime_flexible(fecha_desde)
        fecha_hasta_dt = parse_datetime_flexible(fecha_hasta)
        
        if not fecha_desde_dt or not fecha_hasta_dt:
            print("Error: Formato de fecha inválido")
            return None
            
        if fecha_desde_dt > fecha_hasta_dt:
            print("Error: La fecha de inicio no puede ser posterior a la fecha de fin")
            return None
            
    except Exception as e:
        print(f"Error al procesar las fechas: {str(e)}")
        return None
    
    # Intentar hasta max_retries veces
    for attempt in range(max_retries):
        try:
            # Obtener el endpoint correcto según el tipo de activo
            url = obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada)
            if not url:
                print(f"No se pudo determinar el endpoint para el mercado: {mercado}")
                return None
                
            print(f"Obteniendo datos históricos de: {url}")
            
            # Configurar los encabezados de autenticación
            headers = obtener_encabezado_autorizacion(token_portador)
            
            # Realizar la solicitud con un timeout razonable
            response = requests.get(url, headers=headers, timeout=(15, 60))  # 15s conexión, 60s lectura
            
            # Verificar si la respuesta fue exitosa
            if response.status_code == 200:
                # Intentar parsear la respuesta JSON
                try:
                    data = response.json()
                except ValueError as e:
                    print(f"Error al decodificar la respuesta JSON: {e}")
                    print(f"Respuesta del servidor: {response.text[:500]}")
                    
                    # Intentar extraer datos de la respuesta aunque no sea JSON válido
                    if response.text.strip():
                        try:
                            # Intentar con diferentes codificaciones
                            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                                try:
                                    data = response.content.decode(encoding)
                                    if data.strip():
                                        print(f"Respuesta decodificada con {encoding}: {data[:200]}...")
                                        # Intentar parsear como JSON si parece serlo
                                        if data.strip().startswith('{') or data.strip().startswith('['):
                                            data = json.loads(data)
                                            break
                                        else:
                                            # Si no es JSON, devolver como texto plano
                                            return pd.Series([float(x) for x in data.split() if x.replace('.', '').isdigit()])
                                except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                                    continue
                            
                            if isinstance(data, str):
                                print("No se pudo convertir la respuesta a un formato manejable")
                                return None
                                
                        except Exception as parse_error:
                            print(f"Error al procesar la respuesta: {str(parse_error)}")
                            return None
                    
                    # Si llegamos aquí, no se pudo procesar la respuesta
                    if attempt < max_retries - 1:
                        print(f"Reintentando... (Intento {attempt + 2}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 60)  # Backoff exponencial, máximo 60 segundos
                        continue
                    return None
                
                # Verificar si la respuesta indica un error
                if isinstance(data, dict):
                    if 'error' in data or 'status' in data and data.get('status') == 'error':
                        error_msg = data.get('error', data.get('message', 'Error desconocido en la API'))
                        print(f"Error en la respuesta de la API: {error_msg}")
                        
                        # Manejo específico de errores conocidos
                        if "no cotiza" in str(error_msg).lower() or "no existe" in str(error_msg).lower():
                            return None
                        
                        # Reintentar si es un error temporal
                        if attempt < max_retries - 1 and any(keyword in str(error_msg).lower() 
                                                         for keyword in ['temporal', 'temporalmente', 'reintentar']):
                            print(f"Reintentando en {retry_delay} segundos...")
                            time.sleep(retry_delay)
                            retry_delay = min(retry_delay * 2, 60)
                            continue
                        
                        return None
                
                # Procesar los datos históricos
                print(f"Procesando {len(data) if hasattr(data, '__len__') else 1} registros...")
                serie = procesar_respuesta_historico(data, mercado)
                
                if serie is not None and not serie.empty:
                    # Verificar que la serie tenga datos en el rango solicitado
                    if not serie.empty and len(serie) > 0:
                        print(f"Datos históricos obtenidos correctamente: {len(serie)} puntos de datos")
                        return serie
                    else:
                        print("La serie está vacía o no contiene datos en el rango especificado")
                        return None
                else:
                    print(f"No se pudieron procesar los datos históricos para {simbolo}")
                    print(f"Tipo de datos recibido: {type(data)}")
                    print(f"Muestra de datos: {str(data)[:300]}..." if data else "Sin datos")
                    return None
                    
            elif response.status_code == 401:  # No autorizado
                print("Error de autenticación: Token inválido o expirado")
                # No tiene sentido reintentar con el mismo token
                return None
                
            elif response.status_code == 403:  # Prohibido
                print("Acceso denegado: No tiene permisos para acceder a este recurso")
                return None
                
            elif response.status_code == 404:  # No encontrado
                print(f"Recurso no encontrado: {url}")
                return None
                
            elif response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', retry_delay))
                print(f"Límite de tasa excedido. Reintentando en {retry_after} segundos...")
                time.sleep(retry_after)
                retry_delay = min(retry_delay * 2, 60)  # Aumentar el retraso para el próximo intento
                continue
                
            elif 500 <= response.status_code < 600:  # Errores del servidor
                print(f"Error del servidor ({response.status_code}). Reintentando en {retry_delay} segundos...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)
                    continue
                
            else:
                print(f"Error en la solicitud HTTP: {response.status_code} - {response.reason}")
                print(f"Respuesta: {response.text[:500]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Tiempo de espera agotado al intentar conectar con el servidor (intento {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
            continue
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Reintentando en {retry_delay} segundos... (Intento {attempt + 2}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Backoff exponencial, máximo 60 segundos
            continue
        
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    return None

def obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Devuelve el endpoint correcto según el tipo de activo
    """
    base_url = "https://api.invertironline.com/api/v2"
    
    # Mapeo de mercados a sus respectivos endpoints
    endpoints = {
        'Opciones': f"{base_url}/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'FCI': f"{base_url}/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'MEP': f"{base_url}/Cotizaciones/MEP/{simbolo}",
        'Caucion': f"{base_url}/Cotizaciones/Cauciones/Todas/Argentina",
        'TitulosPublicos': f"{base_url}/TitulosPublicos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Cedears': f"{base_url}/Cedears/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'ADRs': f"{base_url}/ADRs/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Bonos': f"{base_url}/Bonos/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
    }
    
    # Intentar determinar automáticamente el tipo de activo si no se especifica
    if mercado not in endpoints:
        if simbolo.endswith(('.BA', '.AR')):
            return endpoints.get('Cedears')
        elif any(ext in simbolo.upper() for ext in ['AL', 'GD', 'AY24', 'GD30', 'AL30']):
            return endpoints.get('Bonos')
        else:
            # Por defecto, asumimos que es un título regular
            return f"{base_url}/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    
    return endpoints.get(mercado)

def procesar_respuesta_historico(data, tipo_activo):
    """
    Procesa la respuesta de la API según el tipo de activo, manejando diferentes formatos de respuesta.
    
    Args:
        data: Datos de respuesta de la API (puede ser lista, diccionario o valor único)
        tipo_activo (str): Tipo de activo (ej: 'acciones', 'bonos', 'fci', 'opciones')
        
    Returns:
        pd.Series: Serie temporal con los precios históricos o None en caso de error
    """
    if not data:
        print("Datos de respuesta vacíos")
        return None
    
    try:
        # Para series históricas en formato lista
        if isinstance(data, list):
            return _procesar_respuesta_lista(data, tipo_activo)
            
        # Para respuestas en formato diccionario
        elif isinstance(data, dict):
            # Verificar si hay una clave que contenga los datos principales
            if 'datos' in data:
                return _procesar_respuesta_lista(data['datos'], tipo_activo)
            elif 'titulos' in data and isinstance(data['titulos'], list):
                return _procesar_respuesta_lista(data['titulos'], tipo_activo)
            elif 'ultimaCotizacion' in data:
                return _procesar_respuesta_ultima_cotizacion(data['ultimaCotizacion'])
            else:
                # Intentar extraer datos del diccionario directamente
                return _procesar_respuesta_dict(data, tipo_activo)
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            return pd.Series([float(data)], index=[pd.Timestamp.now()], name='precio')
            
        # Para respuestas en formato string (convertir a numérico si es posible)
        elif isinstance(data, str):
            try:
                valor = float(data)
                return pd.Series([valor], index=[pd.Timestamp.now()], name='precio')
            except (ValueError, TypeError):
                print(f"No se pudo convertir el valor a numérico: {data}")
                return None
                
        print(f"Formato de respuesta no soportado: {type(data)}")
        return None
        
    except Exception as e:
        print(f"Error al procesar respuesta histórica: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def _procesar_respuesta_lista(datos, tipo_activo):
    """Procesa una respuesta en formato lista"""
    precios = []
    fechas = []
    
    for item in datos:
        try:
            # Manejar diferentes estructuras de respuesta
            if isinstance(item, dict):
                # Buscar el precio en diferentes campos comunes
                precio = None
                for campo in ['ultimoPrecio', 'precio', 'valor', 'cierre', 'cierreAjustado', 
                             'close', 'last', 'valorCuotaparte', 'valorCuotaParte']:
                    if campo in item and item[campo] is not None:
                        try:
                            precio = float(item[campo])
                            if precio > 0:
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Si no se encontró un precio válido, intentar con otros campos
                if precio is None or precio <= 0:
                    for campo in ['cierreAnterior', 'precioPromedio', 'apertura', 'open', 'high', 'low']:
                        if campo in item and item[campo] is not None:
                            try:
                                precio = float(item[campo])
                                if precio > 0:
                                    break
                            except (ValueError, TypeError):
                                continue
                
                # Si aún no hay precio, saltar este ítem
                if precio is None or precio <= 0:
                    continue
                
                # Buscar la fecha en diferentes campos
                fecha_str = None
                for campo in ['fechaHora', 'fecha', 'date', 'fechaCotizacion', 'fechaOperacion']:
                    if campo in item and item[campo] is not None:
                        fecha_str = item[campo]
                        break
                
                if fecha_str:
                    fecha_parsed = parse_datetime_flexible(fecha_str)
                    if fecha_parsed is not None:
                        precios.append(precio)
                        fechas.append(fecha_parsed)
                        
        except (ValueError, AttributeError, TypeError) as e:
            print(f"Error al procesar ítem: {str(e)}")
            continue
    
    if precios and fechas:
        serie = pd.Series(precios, index=fechas, name='precio')
        # Eliminar duplicados manteniendo el último valor
        serie = serie[~serie.index.duplicated(keep='last')]
        # Ordenar por fecha
        return serie.sort_index()
    
    print("No se encontraron datos válidos en la respuesta")
    return None

def _procesar_respuesta_dict(datos, tipo_activo):
    """Procesa una respuesta en formato diccionario"""
    try:
        # Intentar extraer campos comunes
        precio = None
        fecha_str = None
        
        # Buscar precio en campos comunes
        for campo in ['ultimoPrecio', 'precio', 'valor', 'cierre', 'cierreAjustado', 'valorCuotaparte']:
            if campo in datos and datos[campo] is not None:
                try:
                    precio = float(datos[campo])
                    if precio > 0:
                        break
                except (ValueError, TypeError):
                    continue
        
        # Buscar fecha en campos comunes
        for campo in ['fechaHora', 'fecha', 'fechaCotizacion', 'fechaActualizacion']:
            if campo in datos and datos[campo] is not None:
                fecha_str = datos[campo]
                break
        
        if precio is not None and precio > 0 and fecha_str:
            fecha_parsed = parse_datetime_flexible(fecha_str)
            if fecha_parsed is not None:
                return pd.Series([precio], index=[fecha_parsed], name='precio')
    
    except Exception as e:
        print(f"Error al procesar diccionario: {str(e)}")
    
    return None

def _procesar_respuesta_ultima_cotizacion(datos):
    """Procesa la respuesta de última cotización"""
    try:
        if not isinstance(datos, dict):
            return None
            
        precio = None
        fecha_str = None
        
        # Buscar precio en campos comunes
        for campo in ['precio', 'valor', 'valorCuotaparte', 'ultimoPrecio']:
            if campo in datos and datos[campo] is not None:
                try:
                    precio = float(datos[campo])
                    if precio > 0:
                        break
                except (ValueError, TypeError):
                    continue
        
        # Buscar fecha en campos comunes
        for campo in ['fecha', 'fechaHora', 'fechaCotizacion']:
            if campo in datos and datos[campo] is not None:
                fecha_str = datos[campo]
                break
        
        if precio is not None and precio > 0 and fecha_str:
            fecha_parsed = parse_datetime_flexible(fecha_str)
            if fecha_parsed is not None:
                return pd.Series([precio], index=[fecha_parsed], name='precio')
    
    except Exception as e:
        print(f"Error al procesar última cotización: {str(e)}")
    
    return None

def obtener_encabezado_autorizacion(token_portador):
    return {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }

def parse_datetime_flexible(datetime_string):
    """
    Intenta parsear una cadena de fecha/hora en varios formatos comunes.
    
    Args:
        datetime_string: Cadena de fecha/hora a parsear (str, int, float, datetime, Timestamp)
        
    Returns:
        datetime: Objeto datetime con la fecha/hora parseada, o None si no se pudo parsear
    """
    if not datetime_string and not isinstance(datetime_string, (int, float)):
        return None
        
    # Si ya es un objeto datetime o Timestamp, devolverlo directamente
    if isinstance(datetime_string, (datetime, pd.Timestamp)):
        return datetime_string
        
    # Si es un número (timestamp), convertirlo
    if isinstance(datetime_string, (int, float)):
        try:
            # Intentar primero como milisegundos (más común en APIs)
            if datetime_string > 1e12:  # Si es mayor que el año 33658
                return datetime.fromtimestamp(datetime_string / 1000.0)
            else:
                return datetime.fromtimestamp(datetime_string)
        except (ValueError, OSError) as e:
            print(f"Error al convertir timestamp {datetime_string}: {str(e)}")
            return None
    
    # Asegurarse de que es string
    datetime_str = str(datetime_string).strip()
    
    # Lista de formatos a intentar (ordenados de más específicos a más genéricos)
    formats = [
        # ISO 8601 con timezone
        '%Y-%m-%dT%H:%M:%S.%f%z',  # 2023-04-15T14:30:45.123456-03:00
        '%Y-%m-%dT%H:%M:%S%z',     # 2023-04-15T14:30:45-0300
        
        # ISO 8601 sin timezone
        '%Y-%m-%dT%H:%M:%S.%f',    # 2023-04-15T14:30:45.123456
        '%Y-%m-%d %H:%M:%S.%f',    # 2023-04-15 14:30:45.123456
        
        # Formatos estándar
        '%Y-%m-%dT%H:%M:%S',       # 2023-04-15T14:30:45
        '%Y-%m-%d %H:%M:%S',       # 2023-04-15 14:30:45
        
        # Formatos de fecha con diferentes separadores
        '%Y/%m/%d %H:%M:%S',       # 2023/04/15 14:30:45
        '%d-%m-%Y %H:%M:%S',       # 15-04-2023 14:30:45
        '%d/%m/%Y %H:%M:%S',       # 15/04/2023 14:30:45
        '%m-%d-%Y %H:%M:%S',       # 04-15-2023 14:30:45
        '%m/%d/%Y %H:%M:%S',       # 04/15/2023 14:30:45
        
        # Solo fecha
        '%Y-%m-%d',                # 2023-04-15
        '%d-%m-%Y',                # 15-04-2023
        '%d/%m/%Y',                # 15/04/2023
        '%m-%d-%Y',                # 04-15-2023
        '%m/%d/%Y',                # 04/15/2023
        '%Y%m%d',                  # 20230415
        
        # Formatos con nombres de mes
        '%d-%b-%y',                # 15-Apr-23
        '%d-%b-%Y',                # 15-Apr-2023
        '%d %b %Y',                # 15 Apr 2023
        '%d %B %Y',                # 15 April 2023
        
        # Formatos con hora en 12h
        '%Y-%m-%d %I:%M:%S %p',    # 2023-04-15 02:30:45 PM
        '%m/%d/%Y %I:%M %p',       # 04/15/2023 02:30 PM
    ]
    
    # Intentar con cada formato
    for fmt in formats:
        try:
            # Intentar parsear con el formato actual
            parsed = datetime.strptime(datetime_str, fmt)
            
            # Si el año es muy antiguo o futuro, probablemente sea un error de formato
            current_year = datetime.now().year
            if not (1900 <= parsed.year <= current_year + 2):
                continue
                
            return parsed
            
        except ValueError:
            continue
    
    # Intentar con dateutil.parser si está disponible (más flexible pero más lento)
    try:
        from dateutil import parser
        parsed = parser.parse(datetime_str)
        # Verificar que el año sea razonable
        current_year = datetime.now().year
        if 1900 <= parsed.year <= current_year + 2:
            return parsed
    except (ImportError, ValueError, OverflowError) as e:
        pass
    
    # Si no se pudo parsear con ningún formato conocido
    print(f"No se pudo parsear la fecha: {datetime_string}")
    return None

def obtener_fcis(bearer_token):
    url = "https://api.invertironline.com/api/v2/Titulos/FCI"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener FCIs: {response.status_code}")
        print(response.text)
        return None

def obtener_fci_por_simbolo(simbolo, bearer_token):
    url = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener FCI {simbolo}: {response.status_code}")
        print(response.text)
        return None

def obtener_tipos_fondos(bearer_token):
    url = "https://api.invertironline.com/api/v2/Titulos/FCI/TipoFondos"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener tipos de fondos: {response.status_code}")
        print(response.text)
        return None

def obtener_test_inversor(bearer_token: str) -> Optional[Dict]:
    """Obtiene las opciones disponibles para el test de perfil de inversor"""
    url = "https://api.invertironline.com/api/v2/asesores/test-inversor"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener el test de perfil de inversor: {response.status_code}")
        print(response.text)
        return None

def enviar_respuestas_test(bearer_token: str, respuestas: Dict) -> Optional[Dict]:
    """Envía las respuestas del test de perfil de inversor"""
    url = "https://api.invertironline.com/api/v2/asesores/test-inversor"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.post(url, json=respuestas, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al enviar las respuestas del test: {response.status_code}")
        print(response.text)
        return None

def obtener_administradoras(bearer_token):
    url = "https://api.invertironline.com/api/v2/Titulos/FCI/Administradoras"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener administradoras: {response.status_code}")
        print(response.text)
        return None

def analizar_perfil_portafolio(portafolio_df: pd.DataFrame) -> Dict:
    """
    Analiza la composición del portafolio y sugiere un perfil de inversor.
    
    Args:
        portafolio_df: DataFrame con los activos del portafolio
        
    Returns:
        Dict con el perfil sugerido, composición actual y mensaje
    """
    # Verificar si el DataFrame está vacío
    if portafolio_df is None or portafolio_df.empty:
        return {
            'perfil_sugerido': 'SIN_DATOS',
            'mensaje': 'No hay datos suficientes para analizar el portafolio.',
            'composicion_actual': {}
        }
    
    # Verificar columnas necesarias
    columnas_necesarias = ['tipo', 'valorMercado']
    columnas_faltantes = [col for col in columnas_necesarias if col not in portafolio_df.columns]
    
    if columnas_faltantes:
        print(f"Advertencia: Columnas faltantes en el portafolio: {', '.join(columnas_faltantes)}")
        print("Columnas disponibles:", portafolio_df.columns.tolist())
        
        # Intentar con nombres alternativos de columnas
        mapeo_columnas = {
            'tipo': next((col for col in ['tipo', 'type', 'assetType'] if col in portafolio_df.columns), None),
            'valorMercado': next((col for col in ['valorMercado', 'marketValue', 'currentValue', 'valorActual'] 
                               if col in portafolio_df.columns), None)
        }
        
        if None in mapeo_columnas.values():
            return {
                'perfil_sugerido': 'NO_DETERMINADO',
                'mensaje': f'No se pueden analizar los datos. Faltan columnas requeridas: {columnas_faltantes}',
                'composicion_actual': {}
            }
        
        # Renombrar columnas temporalmente
        portafolio_df = portafolio_df.rename(columns={
            mapeo_columnas['tipo']: 'tipo',
            mapeo_columnas['valorMercado']: 'valorMercado'
        })
    
    try:
        # Calcular composición por tipo de activo
        valor_total = portafolio_df['valorMercado'].sum()
        if valor_total <= 0:
            raise ValueError("El valor total del portafolio debe ser mayor a cero")
            
        composicion = portafolio_df.groupby('tipo')['valorMercado'].sum() / valor_total * 100
        composicion_actual = composicion.to_dict()
        
        # Mapear tipos a categorías más amplias (insensible a mayúsculas/minúsculas)
        composicion_lower = {k.upper(): v for k, v in composicion_actual.items()}
        
        renta_fija = sum(v for k, v in composicion_lower.items() 
                        if any(term in k for term in ['BONO', 'LETRA', 'FIDEICOMISO', 'OBLIGACION', 'TITULO', 'PUBLICO']))
        
        renta_variable = sum(v for k, v in composicion_lower.items() 
                           if any(term in k for term in ['ACCION', 'CEDEAR', 'ETF', 'ACCIONES', 'ACCIONARIA']))
        
        renta_mixta = sum(v for k, v in composicion_lower.items() 
                         if any(term in k for term in ['FCI', 'FONDO', 'MIXTO', 'BALANCEADO']))
        
        # Normalizar para que sumen 100%
        total = renta_fija + renta_variable + renta_mixta
        if total > 0:
            factor = 100 / total
            renta_fija *= factor
            renta_variable *= factor
            renta_mixta *= factor
        
        # Determinar perfil basado en la composición
        if renta_fija >= 70:
            perfil = 'CONSERVADOR'
        elif renta_variable >= 40:
            perfil = 'ARRIESGADO'
        else:
            perfil = 'MODERADO'
        
        return {
            'perfil_sugerido': perfil,
            'composicion_actual': {
                'Renta Fija': round(renta_fija, 2),
                'Renta Mixta': round(renta_mixta, 2),
                'Renta Variable': round(renta_variable, 2)
            },
            'mensaje': f'El portafolio actual sugiere un perfil {perfil}.'
        }
        
    except Exception as e:
        print(f"Error al analizar el perfil del portafolio: {str(e)}")
        return {
            'perfil_sugerido': 'ERROR',
            'mensaje': f'Error al analizar el portafolio: {str(e)}',
            'composicion_actual': {}
        }

def recomendar_fcis_por_perfil(perfil: str, fcis_disponibles: pd.DataFrame) -> pd.DataFrame:
    """Recomienda FCIs basados en el perfil del inversor"""
    if perfil not in PERFILES_INVERSOR:
        perfil = 'MODERADO'  # Perfil por defecto
    
    # Filtrar FCIs según el perfil
    if perfil == 'CONSERVADOR':
        fcis_filtrados = fcis_disponibles[
            (fcis_disponibles['perfilInversor'].str.contains('Conservador', case=False)) |
            (fcis_disponibles['tipoFondo'].str.contains('Renta Fija', case=False))
        ]
    elif perfil == 'ARRIESGADO':
        fcis_filtrados = fcis_disponibles[
            (fcis_disponibles['perfilInversor'].str.contains('Arriesgado|Agresivo', case=False)) |
            (fcis_disponibles['tipoFondo'].str.contains('Renta Variable', case=False))
        ]
    else:  # MODERADO
        fcis_filtrados = fcis_disponibles[
            (fcis_disponibles['perfilInversor'].str.contains('Moderado', case=False)) |
            (fcis_disponibles['tipoFondo'].str.contains('Mixto', case=False))
        ]
    
    # Ordenar por rentabilidad reciente (si está disponible)
    if 'rentabilidadUltimos30Dias' in fcis_filtrados.columns:
        return fcis_filtrados.sort_values('rentabilidadUltimos30Dias', ascending=False)
    return fcis_filtrados
        
def obtener_portafolio(bearer_token):
    """
    Obtiene el portafolio actual del cliente
    
    Args:
        bearer_token: Token de autenticación
        
    Returns:
        dict or None: Datos del portafolio o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/portafolio/argentina"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    
    print("\nSolicitando datos del portafolio...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        portafolio = response.json()
        
        # Verificar la estructura de la respuesta
        if 'activos' in portafolio and portafolio['activos']:
            print(f"Se encontraron {len(portafolio['activos'])} activos en el portafolio")
            # Mostrar los primeros activos para depuración
            for i, activo in enumerate(portafolio['activos'][:3], 1):
                print(f"\nActivo {i}:")
                for key, value in activo.items():
                    print(f"  {key}: {value}")
        else:
            print("No se encontraron activos en el portafolio")
            
        return portafolio
    else:
        print(f"Error al obtener el portafolio: {response.status_code}")
        print("Respuesta del servidor:", response.text)
        return None

def calcular_estadisticas_portafolio(portafolio_df):
    """
    Calcula estadísticas básicas del portafolio.
    
    Args:
        portafolio_df: DataFrame con los activos del portafolio
        
    Returns:
        dict: Diccionario con las estadísticas calculadas
    """
    if portafolio_df is None or portafolio_df.empty:
        print("Advertencia: El DataFrame del portafolio está vacío o es None")
        return {}
    
    # Mostrar las columnas disponibles para depuración
    print("\nColumnas disponibles en el portafolio:", portafolio_df.columns.tolist())
    
    # Mapeo de posibles nombres de columnas para diferentes versiones de la API
    col_valor = next((col for col in ['valorMercado', 'marketValue', 'currentValue'] 
                     if col in portafolio_df.columns), None)
    col_rent = next((col for col in ['rentabilidadPorcentaje', 'returnPercentage', 'performance'] 
                    if col in portafolio_df.columns), None)
    
    if col_valor is None:
        print("Advertencia: No se encontró la columna de valor en el portafolio")
        print("Se intentará calcular el valor a partir de cantidad y precio")
        if 'cantidad' in portafolio_df.columns and 'ultimoPrecio' in portafolio_df.columns:
            portafolio_df['valorCalculado'] = portafolio_df['cantidad'] * portafolio_df['ultimoPrecio']
            col_valor = 'valorCalculado'
    
    # Calcular estadísticas con manejo de columnas faltantes
    stats = {
        'valor_total': portafolio_df[col_valor].sum() if col_valor is not None else None,
        'cantidad_activos': len(portafolio_df)
    }
    
    # Añadir métricas opcionales si están disponibles
    if col_rent is not None:
        stats['rentabilidad_promedio'] = portafolio_df[col_rent].mean()
    
    if 'volatilidadAnual' in portafolio_df.columns:
        stats['volatilidad_promedio'] = portafolio_df['volatilidadAnual'].mean()
    
    if 'sharpeRatio' in portafolio_df.columns:
        stats['sharpe_ratio'] = portafolio_df['sharpeRatio'].mean()
    
    return stats

def optimizar_portafolio(returns, num_portfolios=10000, risk_free_rate=0.05):
    """Optimiza el portafolio usando el modelo de Markowitz"""
    results = np.zeros((3, num_portfolios))
    weights_record = []
    
    for i in range(num_portfolios):
        weights = np.random.random(len(returns.columns))
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_return = np.sum(returns.mean() * weights) * 252
        portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        results[0,i] = portfolio_std_dev
        results[1,i] = portfolio_return
        results[2,i] = (portfolio_return - risk_free_rate) / portfolio_std_dev  # Sharpe Ratio
    
    return results, np.array(weights_record)

def mostrar_grafico_optimizacion(results, returns, weights_record):
    """Muestra el gráfico de optimización del portafolio"""
    max_sharpe_idx = np.argmax(results[2])
    sdp, rp = results[0, max_sharpe_idx], results[1, max_sharpe_idx]
    
    plt.figure(figsize=(12, 8))
    plt.scatter(results[0,:], results[1,:], c=results[2,:], cmap='viridis', marker='o', s=10, alpha=0.3)
    plt.colorbar(label='Sharpe Ratio')
    plt.scatter(sdp, rp, marker='*', color='r', s=500, label='Portafolio Óptimo')
    plt.title('Optimización de Portafolio')
    plt.xlabel('Volatilidad Anualizada')
    plt.ylabel('Retorno Anualizado')
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # Mostrar activos del portafolio óptimo
    optimal_weights = weights_record[max_sharpe_idx]
    optimal_allocation = pd.DataFrame({
        'Activo': returns.columns,
        'Peso': optimal_weights,
        'Retorno Anual': returns.mean() * 252,
        'Volatilidad Anual': returns.std() * np.sqrt(252)
    })
    print("\nAsignación Óptima de Activos:")
    print(optimal_allocation)

def analizar_riesgo(portafolio_df):
    """
    Analiza el perfil de riesgo del portafolio.
    
    Args:
        portafolio_df (pd.DataFrame): DataFrame con los activos del portafolio
        
    Returns:
        dict: Diccionario con el análisis de riesgo
    """
    if portafolio_df is None or portafolio_df.empty:
        return {
            'error': 'El portafolio está vacío',
            'exposicion_por_activo': {},
            'top_riesgos': pd.DataFrame(),
            'advertencias': []
        }
    
    # Hacer una copia para no modificar el dataframe original
    df = portafolio_df.copy()
    advertencias = []
    
    # Verificar columnas requeridas
    columnas_requeridas = {'tipo', 'valorMercado'}
    columnas_faltantes = columnas_requeridas - set(df.columns)
    
    if columnas_faltantes:
        return {
            'error': f'Faltan columnas requeridas: {", ".join(columnas_faltantes)}',
            'exposicion_por_activo': {},
            'top_riesgos': pd.DataFrame(),
            'advertencias': [f'Columnas faltantes: {", ".join(columnas_faltantes)}']
        }
    
    # Manejar valores faltantes o inválidos en valorMercado
    if df['valorMercado'].isna().any() or (df['valorMercado'] <= 0).any():
        advertencias.append('Se encontraron valores inválidos o faltantes en valorMercado. Se reemplazarán por 0.')
        df['valorMercado'] = df['valorMercado'].fillna(0).clip(lower=0)
    
    # Calcular exposición por tipo de activo
    try:
        exposicion = df.groupby('tipo')['valorMercado'].sum()
        total_valor = df['valorMercado'].sum()
        
        if total_valor > 0:
            exposicion_por_activo = (exposicion / total_valor).to_dict()
        else:
            exposicion_por_activo = {}
            advertencias.append('El valor total del portafolio es 0 o negativo')
    except Exception as e:
        exposicion_por_activo = {}
        advertencias.append(f'Error al calcular exposición por activo: {str(e)}')
    
    # Identificar mayores riesgos (top 5 por valor de mercado)
    try:
        columnas_riesgo = ['simbolo', 'valorMercado', 'rentabilidadPorcentaje']
        columnas_disponibles = [col for col in columnas_riesgo if col in df.columns]
        
        if len(columnas_disponibles) < 2:  # Necesitamos al menos símbolo y valorMercado
            top_riesgos = pd.DataFrame(columns=['simbolo', 'valorMercado'])
            advertencias.append('No hay suficientes datos para calcular los mayores riesgos')
        else:
            # Ordenar por valor de mercado descendente y tomar los 5 mayores
            top_riesgos = df.sort_values('valorMercado', ascending=False).head(5)[columnas_disponibles]
    except Exception as e:
        top_riesgos = pd.DataFrame()
        advertencias.append(f'Error al identificar mayores riesgos: {str(e)}')
    
    # Calcular métricas adicionales de riesgo
    try:
        # Calcular concentración (índice Herfindahl-Hirschman)
        if not df.empty and 'valorMercado' in df.columns:
            participacion = df['valorMercado'] / df['valorMercado'].sum()
            hhi = (participacion ** 2).sum() * 10000  # Escalar a 0-10000
            concentracion = {
                'hhi': hhi,
                'nivel': 'Baja concentración' if hhi < 1500 else 
                        'Moderada concentración' if hhi < 2500 else 'Alta concentración'
            }
        else:
            concentracion = {'hhi': None, 'nivel': 'No disponible'}
    except Exception as e:
        concentracion = {'hhi': None, 'nivel': f'Error: {str(e)}'}
        advertencias.append(f'Error al calcular concentración: {str(e)}')
    
    return {
        'exposicion_por_activo': exposicion_por_activo,
        'top_riesgos': top_riesgos,
        'concentracion': concentracion,
        'advertencias': advertencias if advertencias else None,
        'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    # Configuración inicial
    username = "boosandr97@gmail.com"
    password = "Yacanto1997_"
    
    # Obtener tokens de autenticación
    bearer_token, refresh_token = obtener_tokens(username, password)
    
    if not bearer_token:
        print("Error al autenticar. Verifica tus credenciales.")
        return
    
    # 0. Realizar test de perfil de inversor
    print("\n=== TEST DE PERFIL DE INVERSOR ===")
    test_data = obtener_test_inversor(bearer_token)
    perfil_inversor = 'MODERADO'  # Perfil por defecto
    
    if test_data:
        print("Opciones del test de perfil de inversor obtenidas.")
        # Aquí podrías implementar la lógica para mostrar las preguntas y recopilar respuestas
        # Por ahora, usaremos respuestas de ejemplo
        respuestas_ejemplo = {
            "enviarEmailCliente": False,
            "instrumentosInvertidosAnteriormente": [1, 2],
            "nivelesConocimientoInstrumentos": [1],
            "idPlazoElegido": 2,
            "idEdadElegida": 3,
            "idObjetivoInversionElegida": 1,
            "idPolizaElegida": 1,
            "idCapacidadAhorroElegida": 2,
            "idPorcentajePatrimonioDedicado": 2
        }
        
        resultado_test = enviar_respuestas_test(bearer_token, respuestas_ejemplo)
        if resultado_test and 'perfilSugerido' in resultado_test:
            perfil_inversor = resultado_test['perfilSugerido'].get('nombre', 'MODERADO')
            print(f"\nPerfil de inversor identificado: {perfil_inversor}")
            print(f"Detalles: {resultado_test['perfilSugerido'].get('detalle', 'Sin detalles adicionales')}")
        else:
            print("No se pudo determinar el perfil del inversor. Usando perfil moderado por defecto.")
    else:
        print("No se pudo obtener el test de perfil. Usando perfil moderado por defecto.")

    # 1. Obtener y mostrar portafolio actual
    print("\n=== PORTAFOLIO ACTUAL ===")
    portafolio = obtener_portafolio(bearer_token)
    
    if portafolio and 'activos' in portafolio and portafolio['activos']:
        df_portafolio = pd.DataFrame(portafolio['activos'])
        
        # Mostrar información de depuración
        print("\nPrimeras filas del portafolio:")
        print(df_portafolio.head())
        print("\nColumnas disponibles:", df_portafolio.columns.tolist())
        
        # Calcular estadísticas del portafolio
        stats = calcular_estadisticas_portafolio(df_portafolio)
        
        print("\n=== RESUMEN DEL PORTAFOLIO ===")
        if 'valor_total' in stats and stats['valor_total'] is not None:
            print(f"Valor Total: ${stats['valor_total']:,.2f}")
        else:
            print("No se pudo calcular el valor total del portafolio")
            
        print(f"Cantidad de Activos: {stats['cantidad_activos']}")
        
        if 'rentabilidad_promedio' in stats and stats['rentabilidad_promedio'] is not None:
            print(f"Rentabilidad Promedio: {stats['rentabilidad_promedio']:.2f}%")
        
        # Mostrar composición del portafolio (solo columnas existentes)
        print("\n=== COMPOSICIÓN DEL PORTAFOLIO ===")
        columnas_deseadas = ['simbolo', 'tipo', 'descripcion', 'cantidad', 'precioPromedio', 
                            'ultimoPrecio', 'variacionDiaria', 'rentabilidadPorcentaje', 'valorMercado']
        columnas_existentes = [col for col in columnas_deseadas if col in df_portafolio.columns]
        
        if columnas_existentes:
            print(df_portafolio[columnas_existentes].to_string())
        else:
            print("No se encontraron columnas de datos para mostrar.")
        
        # Análisis de perfil del portafolio
        print("\n=== ANÁLISIS DE PERFIL DE INVERSIÓN ===")
        analisis_perfil = analizar_perfil_portafolio(df_portafolio)
        
        if analisis_perfil and 'perfil_sugerido' in analisis_perfil:
            perfil_portafolio = analisis_perfil['perfil_sugerido']
            composicion_actual = analisis_perfil.get('composicion_actual', {})
            
            print(f"\nPerfil sugerido por composición actual: {perfil_portafolio}")
            
            if composicion_actual:
                print("\nComposición actual del portafolio:")
                for tipo, porcentaje in composicion_actual.items():
                    print(f"- {tipo}: {porcentaje:.1f}%")
            
            # Comparar con perfil objetivo
            perfil_objetivo = PERFILES_INVERSOR.get(perfil_inversor, PERFILES_INVERSOR['MODERADO'])
            print(f"\nComparación con perfil objetivo ({perfil_inversor}):")
            
            recomendaciones = []
            for objetivo in perfil_objetivo['composicion']:
                tipo = objetivo['tipo']
                actual = composicion_actual.get(tipo, 0)
                print(f"- {tipo}: {actual:.1f}% (Objetivo: {objetivo['min']}-{objetivo['max']}%)")
                
                # Generar recomendaciones
                if actual < objetivo['min']:
                    recomendaciones.append(f"Aumentar exposición a {tipo}")
                elif actual > objetivo['max']:
                    recomendaciones.append(f"Reducir exposición a {tipo}")
            
            if recomendaciones:
                print("\nRecomendaciones de rebalanceo:")
                for rec in recomendaciones:
                    print(f"- {rec}")
        else:
            print("No se pudo realizar el análisis de perfil del portafolio.")
            perfil_portafolio = 'MODERADO'
        
        # Análisis de riesgo
        print("\n=== ANÁLISIS DE RIESGO ===")
        riesgo = analizar_riesgo(df_portafolio)
        if riesgo:
            if 'exposicion_por_activo' in riesgo and riesgo['exposicion_por_activo']:
                print("\nExposición por Tipo de Activo:")
                print(riesgo['exposicion_por_activo'])
            
            if 'top_riesgos' in riesgo and not riesgo['top_riesgos'].empty:
                print("\nMayores Posiciones por Riesgo:")
                print(riesgo['top_riesgos'])
            else:
                print("No se encontraron datos de riesgo para mostrar.")
    else:
        print("No se encontraron activos en el portafolio o no se pudo acceder a los datos.")
        perfil_portafolio = 'MODERADO'
    
    # 2. Obtener y mostrar FCIs con recomendaciones
    print("\n=== FONDOS COMUNES DE INVERSIÓN ===")
    fcis = obtener_fcis(bearer_token)
    
    if fcis:
        df_fcis = pd.DataFrame(fcis)
        
        # Obtener detalles adicionales de cada FCI
        df_fcis['rentabilidadUltimos30Dias'] = 0.0
        for idx, fci in df_fcis.iterrows():
            detalle = obtener_fci_por_simbolo(fci['simbolo'], bearer_token)
            if detalle and 'rentabilidadUltimos30Dias' in detalle:
                df_fcis.at[idx, 'rentabilidadUltimos30Dias'] = detalle['rentabilidadUltimos30Dias']
        
        # Filtrar solo FCIs que están en el portafolio
        if 'activos' in portafolio and portafolio['activos']:
            fcis_portafolio = [activo['simbolo'] for activo in portafolio['activos'] if activo.get('tipo') == 'FCI']
            if fcis_portafolio:
                df_fcis_portafolio = df_fcis[df_fcis['simbolo'].isin(fcis_portafolio)]
                print("\n=== FCIs EN TU PORTAFOLIO ===")
                print(df_fcis_portafolio[['simbolo', 'descripcion', 'tipoFondo', 'perfilInversor', 'rentabilidadUltimos30Dias', 'plazoLiquidacion']])
                
                # Mostrar detalles de cada FCI
                for _, fci in df_fcis_portafolio.iterrows():
                    print(f"\nDetalle de {fci['simbolo']}:")
                    print(f"Descripción: {fci.get('descripcion', 'N/A')}")
                    print(f"Tipo: {fci.get('tipoFondo', 'N/A')}")
                    print(f"Perfil: {fci.get('perfilInversor', 'N/A')}")
                    print(f"Rentabilidad 30 días: {fci.get('rentabilidadUltimos30Dias', 'N/A')}%")
                    print(f"Plazo de liquidación: {fci.get('plazoLiquidacion', 'N/A')}")
        
        # Mostrar recomendaciones de FCIs según perfil
        print("\n=== RECOMENDACIONES DE FCIs SEGÚN TU PERFIL ===")
        fcis_recomendados = recomendar_fcis_por_perfil(perfil_inversor, df_fcis)
        
        if not fcis_recomendados.empty:
            print(f"\nFCIs recomendados para perfil {perfil_inversor}:")
            print(fcis_recomendados[['simbolo', 'descripcion', 'tipoFondo', 'perfilInversor', 'rentabilidadUltimos30Dias']].head(5))
            
            # Mostrar detalles de los FCIs recomendados
            print("\nDetalles de los FCIs recomendados:")
            for _, fci in fcis_recomendados.head(3).iterrows():
                detalle = obtener_fci_por_simbolo(fci['simbolo'], bearer_token)
                if detalle:
                    print(f"\n{fci['simbolo']} - {fci['descripcion']}")
                    print(f"Administradora: {detalle.get('administradora', 'N/A')}")
                    print(f"Rentabilidad 30 días: {detalle.get('rentabilidadUltimos30Dias', 'N/A')}%")
                    print(f"Patrimonio: ${detalle.get('patrimonio', 0):,.2f}")
                    print(f"Participantes: {detalle.get('cantidadParticipe', 'N/A')}")
        else:
            print("No se encontraron FCIs que coincidan con tu perfil de inversor.")
        
        # Mostrar todos los FCIs disponibles
        print("\n=== TODOS LOS FCIs DISPONIBLES ===")
        print(df_fcis[['simbolo', 'descripcion', 'tipoFondo', 'perfilInversor', 'rentabilidadUltimos30Dias']].head(10))
    
    # 3. Análisis de series históricas para optimización
    print("\n=== ANÁLISIS DE SERIES TEMPORALES ===")
    if 'activos' in portafolio and portafolio['activos']:
        # Tomar los primeros 5 activos para el análisis
        activos_analisis = portafolio['activos'][:5]
        
        # Obtener datos históricos
        precios = {}
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        fecha_desde = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        for activo in activos_analisis:
            simbolo = activo.get('simbolo')
            mercado = activo.get('mercado', 'BCBA')  # Valor por defecto BCBA
            if not simbolo:
                continue  # Saltar si no hay símbolo
            
            # Corregido: usar la función correcta
            datos = obtener_serie_historica_iol(bearer_token, mercado, simbolo, fecha_desde, fecha_hasta, 'ajustada')
            if datos is not None and not datos.empty:
                precios[simbolo] = datos
        
        # Crear DataFrame con los precios
        if precios:
            df_precios = pd.DataFrame(precios)
            
            # Calcular retornos
            retornos = df_precios.pct_change().dropna()
            
            # Optimizar portafolio
            print("\nOptimizando portafolio...")
            resultados, pesos = optimizar_portafolio(retornos)
            mostrar_grafico_optimizacion(resultados, retornos, pesos)
    
    # 4. Mostrar tipos de fondos y administradoras
    print("\n=== INFORMACIÓN ADICIONAL ===")
    
    # Tipos de fondos
    tipos_fondos = obtener_tipos_fondos(bearer_token)
    if tipos_fondos:
        print("\nTipos de Fondos Disponibles:")
        for tipo in tipos_fondos[:5]:  # Mostrar solo los primeros 5
            print(f"- {tipo.get('identificador')}: {tipo.get('nombre')}")
    
    # Administradoras
    administradoras = obtener_administradoras(bearer_token)
    if administradoras:
        print("\nAdministradoras Disponibles:")
        for admin in administradoras[:5]:  # Mostrar solo las primeras 5
            print(f"- {admin}")

if __name__ == "__main__":
    main()
