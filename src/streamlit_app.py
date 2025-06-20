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
    Obtiene series históricas para diferentes tipos de activos con manejo mejorado de errores
    """
    try:
        # Primero intentamos con el endpoint específico del mercado
        url = obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada)
        if not url:
            print(f"No se pudo determinar el endpoint para el símbolo {simbolo}")
            return None
        
        headers = obtener_encabezado_autorizacion(token_portador)
        
        # Configurar un timeout más corto para no bloquear la interfaz
        response = requests.get(url, headers=headers, timeout=10)
        
        # Verificar si la respuesta es exitosa
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get('status') == 'error':
                print(f"Error en la respuesta para {simbolo}: {data.get('message', 'Error desconocido')}")
                return None
                
            # Procesar la respuesta según el tipo de activo
            return procesar_respuesta_historico(data, mercado)
        else:
            print(f"Error {response.status_code} al obtener datos para {simbolo}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión para {simbolo}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error inesperado al procesar {simbolo}: {str(e)}")
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
    Procesa la respuesta de la API según el tipo de activo
    """
    if not data:
        return None
    
    try:
        # Para series históricas estándar
        if isinstance(data, list):
            precios = []
            fechas = []
            
            for item in data:
                try:
                    # Manejar diferentes estructuras de respuesta
                    if isinstance(item, dict):
                        precio = item.get('ultimoPrecio') or item.get('precio') or item.get('valor')
                        if not precio or precio == 0:
                            precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                        
                        fecha_str = item.get('fechaHora') or item.get('fecha')
                        
                        if precio is not None and precio > 0 and fecha_str:
                            fecha_parsed = parse_datetime_flexible(fecha_str)
                            if fecha_parsed is not None:
                                precios.append(float(precio))
                                fechas.append(fecha_parsed)
                except (ValueError, AttributeError) as e:
                    continue
            
            if precios and fechas:
                serie = pd.Series(precios, index=fechas, name='precio')
                serie = serie[~serie.index.duplicated(keep='last')]
                return serie.sort_index()
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            return pd.Series([float(data)], index=[pd.Timestamp.now()], name='precio')
            
        return None
        
    except Exception as e:
        print(f"Error al procesar respuesta histórica: {str(e)}")
        return None

def obtener_encabezado_autorizacion(token_portador):
    return {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }

def parse_datetime_flexible(datetime_string):
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "ISO8601",
        "mixed"
    ]
    
    for fmt in formats_to_try:
        try:
            if fmt == "ISO8601":
                return pd.to_datetime(datetime_string, format='ISO8601')
            elif fmt == "mixed":
                return pd.to_datetime(datetime_string, format='mixed')
            else:
                return pd.to_datetime(datetime_string, format=fmt)
        except Exception:
            continue

    try:
        return pd.to_datetime(datetime_string, infer_datetime_format=True)
    except Exception:
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

def mostrar_grafico_optimizacion(results, returns):
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
    """Analiza el perfil de riesgo del portafolio"""
    if portafolio_df.empty:
        return {}
        
    riesgo = {
        'exposicion_por_activo': portafolio_df.groupby('tipo')['valorMercado'].sum() / portafolio_df['valorMercado'].sum(),
        'top_riesgos': portafolio_df.nlargest(5, 'valorMercado')[['simbolo', 'valorMercado', 'rentabilidadPorcentaje']]
    }
    return riesgo

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
            if 'exposicion_por_activo' in riesgo and not riesgo['exposicion_por_activo'].empty:
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
            simbolo = activo['simbolo']
            mercado = activo.get('mercado', 'BCBA')  # Valor por defecto BCBA
            
            # Obtener datos históricos
            datos = obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, 'Ajustada', bearer_token)
            if datos:
                df_temp = pd.DataFrame(datos)
                if not df_temp.empty and 'ultimoPrecio' in df_temp.columns:
                    precios[simbolo] = df_temp['ultimoPrecio']
        
        # Crear DataFrame con los precios
        if precios:
            df_precios = pd.DataFrame(precios)
            
            # Calcular retornos
            retornos = df_precios.pct_change().dropna()
            
            # Optimizar portafolio
            print("\nOptimizando portafolio...")
            resultados, pesos = optimizar_portafolio(retornos)
            mostrar_grafico_optimizacion(resultados, retornos)
    
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
