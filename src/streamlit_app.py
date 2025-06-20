import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# Configuración de estilo para gráficos
plt.style.use('seaborn')
plt.rcParams['figure.figsize'] = [12, 6]

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
        
def obtener_portafolio(bearer_token):
    """Obtiene el portafolio actual del cliente"""
    url = "https://api.invertironline.com/api/v2/portafolio/argentina"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener el portafolio: {response.status_code}")
        print(response.text)
        return None

def calcular_estadisticas_portafolio(portafolio_df):
    """Calcula estadísticas básicas del portafolio"""
    if portafolio_df.empty:
        return {}
        
    stats = {
        'valor_total': portafolio_df['valorMercado'].sum(),
        'cantidad_activos': len(portafolio_df),
        'rentabilidad_promedio': portafolio_df['rentabilidadPorcentaje'].mean(),
        'volatilidad_promedio': portafolio_df['volatilidadAnual'].mean() if 'volatilidadAnual' in portafolio_df.columns else None,
        'sharpe_ratio': portafolio_df['sharpeRatio'].mean() if 'sharpeRatio' in portafolio_df.columns else None
    }
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

    # 1. Obtener y mostrar portafolio actual
    print("\n=== PORTAFOLIO ACTUAL ===")
    portafolio = obtener_portafolio(bearer_token)
    
    if portafolio and 'activos' in portafolio and portafolio['activos']:
        df_portafolio = pd.DataFrame(portafolio['activos'])
        
        # Calcular estadísticas del portafolio
        stats = calcular_estadisticas_portafolio(df_portafolio)
        print("\nResumen del Portafolio:")
        print(f"Valor Total: ${stats['valor_total']:,.2f}")
        print(f"Cantidad de Activos: {stats['cantidad_activos']}")
        print(f"Rentabilidad Promedio: {stats['rentabilidad_promedio']:.2f}%")
        
        # Mostrar composición del portafolio
        print("\nComposición del Portafolio:")
        print(df_portafolio[['simbolo', 'descripcion', 'cantidad', 'precioPromedio', 'ultimoPrecio', 'variacionDiaria', 'rentabilidadPorcentaje', 'valorMercado']])
        
        # Análisis de riesgo
        riesgo = analizar_riesgo(df_portafolio)
        if riesgo:
            print("\nExposición por Tipo de Activo:")
            print(riesgo['exposicion_por_activo'])
            
            print("\nMayores Posiciones por Riesgo:")
            print(riesgo['top_riesgos'])
    else:
        print("No se encontraron activos en el portafolio.")
    
    # 2. Obtener y mostrar FCIs del portafolio
    print("\n=== FONDOS COMUNES DE INVERSIÓN ===")
    fcis = obtener_fcis(bearer_token)
    
    if fcis:
        df_fcis = pd.DataFrame(fcis)
        
        # Filtrar solo FCIs que están en el portafolio
        if 'activos' in portafolio:
            fcis_portafolio = [activo['simbolo'] for activo in portafolio['activos'] if activo.get('tipo') == 'FCI']
            if fcis_portafolio:
                df_fcis_portafolio = df_fcis[df_fcis['simbolo'].isin(fcis_portafolio)]
                print("\nFCIs en tu Portafolio:")
                print(df_fcis_portafolio[['simbolo', 'descripcion', 'tipoFondo', 'perfilInversor', 'plazoLiquidacion']])
                
                # Mostrar detalles de cada FCI
                for simbolo in fcis_portafolio:
                    detalle = obtener_fci_por_simbolo(simbolo, bearer_token)
                    if detalle:
                        print(f"\nDetalle de {simbolo}:")
                        print(f"Administradora: {detalle.get('administradora', 'N/A')}")
                        print(f"Rentabilidad 30 días: {detalle.get('rentabilidadUltimos30Dias', 'N/A')}%")
                        print(f"Patrimonio: ${detalle.get('patrimonio', 0):,.2f}")
                        print(f"Participantes: {detalle.get('cantidadParticipe', 'N/A')}")
        
        # Mostrar todos los FCIs disponibles
        print("\nTodos los FCIs Disponibles:")
        print(df_fcis[['simbolo', 'descripcion', 'tipoFondo', 'perfilInversor']].head(10))  # Mostrar solo los primeros 10
    
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
