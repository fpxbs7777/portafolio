import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
import scipy.optimize as op
from scipy import stats

def calcular_alpha_beta(returns_activo, returns_benchmark, risk_free_rate=0.0):
    """
    Calcula el alpha y beta de un activo respecto a un benchmark.
    
    Args:
        returns_activo (pd.Series): Retornos diarios del activo
        returns_benchmark (pd.Series): Retornos diarios del benchmark
        risk_free_rate (float): Tasa libre de riesgo anual
        
    Returns:
        tuple: (alpha, beta)
    """
    # Alinear las fechas de ambos retornos
    aligned_data = pd.concat([returns_activo, returns_benchmark], axis=1).dropna()
    if len(aligned_data) < 2:
        return 0.0, 0.0
    
    returns_activo_aligned = aligned_data.iloc[:, 0]
    returns_benchmark_aligned = aligned_data.iloc[:, 1]
    
    # Calcular covarianza y varianza
    cov_matrix = np.cov(returns_activo_aligned, returns_benchmark_aligned)
    beta = cov_matrix[0, 1] / cov_matrix[1, 1]
    
    # Calcular alpha (anualizado)
    avg_return_activo = returns_activo_aligned.mean() * 252
    avg_return_benchmark = returns_benchmark_aligned.mean() * 252
    alpha = (avg_return_activo - risk_free_rate) - beta * (avg_return_benchmark - risk_free_rate)
    
    return alpha, beta

def obtener_datos_benchmark(fecha_desde, fecha_hasta, ticker='^MERV'):
    """
    Obtiene datos históricos del benchmark (MERVAL por defecto) usando yfinance.
    
    Args:
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        ticker (str): Ticker del benchmark (por defecto: '^MERV')
        
    Returns:
        pd.DataFrame: DataFrame con los precios históricos del benchmark
    """
    try:
        df = yf.download(ticker, start=fecha_desde, end=fecha_hasta)
        return df['Close']
    except Exception as e:
        print(f"Error al obtener datos del benchmark {ticker}: {str(e)}")
        return None

def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión usando datos históricos.
    
    Args:
        portafolio (dict): Diccionario con los activos y sus cantidades
        valor_total (float): Valor total del portafolio
        token_portador (str): Token de autenticación para la API de InvertirOnline
        dias_historial (int): Número de días de histórico a considerar (por defecto: 252 días hábiles)
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    if not isinstance(portafolio, dict) or not portafolio or valor_total <= 0:
        return {}

    # Obtener fechas para el histórico
    fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    fecha_desde = (datetime.now() - timedelta(days=dias_historial*1.5)).strftime('%Y-%m-%d')
    
    # 1. Calcular concentración del portafolio (Índice de Herfindahl-Hirschman normalizado)
    if len(portafolio) == 0:
        concentracion = 0
    elif len(portafolio) == 1:
        concentracion = 1.0
    else:
        sum_squares = sum((activo.get('Valuación', 0) / valor_total) ** 2 
                         for activo in portafolio.values())
        # Normalizar entre 0 y 1
        min_concentration = 1.0 / len(portafolio)
        concentracion = (sum_squares - min_concentration) / (1 - min_concentration)
    
    # Inicializar estructuras para cálculos
    retornos_diarios = {}
    metricas_activos = {}
    
    # 2. Obtener datos históricos y calcular métricas por activo
    for simbolo, activo in portafolio.items():
        try:
            # Obtener datos históricos usando el método estándar
            mercado = activo.get('mercado', 'BCBA')
            tipo_activo = activo.get('Tipo', 'Desconocido')
            
            # Debug: Mostrar información del activo que se está procesando
            print(f"\nProcesando activo: {simbolo} (Mercado: {mercado}, Tipo: {tipo_activo})")
            
            # Obtener la serie histórica
            try:
                df_historico = obtener_serie_historica_iol(
                    token_portador=token_portador,
                    mercado=mercado,
                    simbolo=simbolo,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    ajustada="SinAjustar"
                )
            except Exception as e:
                print(f"Error al obtener datos históricos para {simbolo}: {str(e)}")
                continue
            
            if df_historico is None:
                print(f"No se obtuvieron datos para {simbolo} (None)")
                continue
                
            if df_historico.empty:
                print(f"Datos vacíos para {simbolo}")
                continue
            
            # Asegurarse de que tenemos las columnas necesarias
            if 'fecha' not in df_historico.columns or 'precio' not in df_historico.columns:
                print(f"Faltan columnas necesarias en los datos de {simbolo}")
                print(f"Columnas disponibles: {df_historico.columns.tolist()}")
                continue
                
            print(f"Datos obtenidos: {len(df_historico)} registros desde {df_historico['fecha'].min()} hasta {df_historico['fecha'].max()}")
                
            # Ordenar por fecha y limpiar duplicados
            df_historico = df_historico.sort_values('fecha')
            df_historico = df_historico.drop_duplicates(subset=['fecha'], keep='last')
            
            # Calcular retornos diarios
            df_historico['retorno'] = df_historico['precio'].pct_change()
            
            # Filtrar valores atípicos usando un enfoque más robusto
            if len(df_historico) > 5:  # Necesitamos suficientes puntos para el filtrado
                q_low = df_historico['retorno'].quantile(0.01)
                q_high = df_historico['retorno'].quantile(0.99)
                df_historico = df_historico[
                    (df_historico['retorno'] >= q_low) & 
                    (df_historico['retorno'] <= q_high)
                ]
            
            # Filtrar valores no finitos y asegurar suficientes datos
            retornos_validos = df_historico['retorno'].replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            
            if len(retornos_validos) < 5:  # Mínimo de datos para métricas confiables
                print(f"No hay suficientes datos válidos para {simbolo} (solo {len(retornos_validos)} registros)")
                continue
                
            # Verificar si hay suficientes variaciones de precio
            if retornos_validos.nunique() < 2:
                print(f"No hay suficiente variación en los precios de {simbolo}")
                continue
            
            # Calcular métricas básicas
            retorno_medio = retornos_validos.mean() * 252  # Anualizado
            volatilidad = retornos_validos.std() * np.sqrt(252)  # Anualizada
            
            # Asegurar valores razonables
            retorno_medio = np.clip(retorno_medio, -5, 5)  # Límite de ±500% anual
            volatilidad = min(volatilidad, 3)  # Límite de 300% de volatilidad
            
            # Calcular métricas de riesgo basadas en la distribución de retornos
            ret_pos = retornos_validos[retornos_validos > 0]
            ret_neg = retornos_validos[retornos_validos < 0]
            n_total = len(retornos_validos)
            
            # Calcular probabilidades
            prob_ganancia = len(ret_pos) / n_total if n_total > 0 else 0.5
            prob_perdida = len(ret_neg) / n_total if n_total > 0 else 0.5
            
            # Calcular probabilidades de movimientos extremos
            prob_ganancia_10 = len(ret_pos[ret_pos > 0.1]) / n_total if n_total > 0 else 0
            prob_perdida_10 = len(ret_neg[ret_neg < -0.1]) / n_total if n_total > 0 else 0
            
            # Calcular el peso del activo en el portafolio
            peso = activo.get('Valuación', 0) / valor_total if valor_total > 0 else 0
            
            # Obtener datos del benchmark (MERVAL) para calcular alpha y beta
            alpha_anual = None
            beta = None
            try:
                # Obtener fechas del activo
                fechas_activo = df_historico['fecha'].dt.normalize()
                fecha_min = fechas_activo.min().strftime('%Y-%m-%d')
                fecha_max = fechas_activo.max().strftime('%Y-%m-%d')
                
                # Obtener datos del benchmark para el mismo período
                precios_benchmark = obtener_datos_benchmark(fecha_min, fecha_max, '^MERV')
                if precios_benchmark is not None and not precios_benchmark.empty:
                    # Calcular retornos diarios del benchmark
                    retornos_benchmark = precios_benchmark.pct_change().dropna()
                    
                    # Asegurar que tengamos los mismos índices para el activo y el benchmark
                    retornos_activo_series = pd.Series(
                        df_historico.set_index('fecha')['retorno'].dropna(),
                        name='activo'
                    )
                    
                    # Alinear las fechas de los retornos
                    retornos_aligned = pd.concat([
                        retornos_activo_series.rename('activo'),
                        retornos_benchmark.rename('benchmark')
                    ], axis=1).dropna()
                    
                    if not retornos_aligned.empty and len(retornos_aligned) > 5:  # Mínimo de datos
                        # Calcular alpha y beta usando la función auxiliar
                        alpha_anual, beta = calcular_alpha_beta(
                            retornos_aligned['activo'],
                            retornos_benchmark,
                            risk_free_rate=0.0  # Tasa libre de riesgo anual (0% por defecto)
                        )
            except Exception as e:
                print(f"Error al calcular alpha/beta para {simbolo}: {str(e)}")
            
            # Guardar métricas
            metricas_activos[simbolo] = {
                'retorno_medio': retorno_medio,
                'volatilidad': volatilidad,
                'prob_ganancia': prob_ganancia,
                'prob_perdida': prob_perdida,
                'prob_ganancia_10': prob_ganancia_10,
                'prob_perdida_10': prob_perdida_10,
                'peso': peso,
                'alpha_anual': alpha_anual if alpha_anual is not None else 0,
                'beta': beta if beta is not None else 0
            }
            
            # Guardar retornos para cálculo de correlaciones
            retornos_diarios[simbolo] = df_historico.set_index('fecha')['retorno']
            
            # Mostrar métricas calculadas para depuración
            print(f"Métricas calculadas para {simbolo}:")
            print(f"- Retorno medio anual: {metricas_activos[simbolo]['retorno_medio']:.2%}")
            print(f"- Volatilidad anual: {metricas_activos[simbolo]['volatilidad']:.2%}")
            print(f"- Alpha anual: {metricas_activos[simbolo].get('alpha_anual', 'N/A')}")
            print(f"- Beta: {metricas_activos[simbolo].get('beta', 'N/A')}")
            
            # Calcular retornos acumulados para el gráfico
            try:
                retornos_diarios = df_historico.set_index('fecha')['retorno'].dropna()
                retornos_acumulados = (1 + retornos_diarios).cumprod() - 1
                metricas_activos[simbolo]['retornos_acumulados'] = retornos_acumulados
            except Exception as e:
                print(f"Error al calcular retornos acumulados para {simbolo}: {str(e)}")
                metricas_activos[simbolo]['retornos_acumulados'] = None
            
        except Exception as e:
            print(f"Error procesando {simbolo}: {str(e)}")
            continue
    
    if not metricas_activos:
        print("No se pudieron calcular métricas para ningún activo")
        return {
            'concentracion': concentracion,
            'std_dev_activo': 0,
            'retorno_esperado_anual': 0,
            'pl_esperado_min': 0,
            'pl_esperado_max': 0,
            'probabilidades': {'perdida': 0, 'ganancia': 0, 'perdida_mayor_10': 0, 'ganancia_mayor_10': 0},
            'riesgo_anual': 0
        }

def obtener_cauciones(token_acceso):
    """
    Obtiene los datos de cauciones de la API de IOL.
    
    Args:
        token_acceso (str): Token de acceso a la API de IOL
        
    Returns:
        pd.DataFrame: DataFrame con los datos de cauciones
    """
    try:
        url = "https://api.invertironline.com/api/v2/operaciones/cauciones"
        headers = {
            'Authorization': f'Bearer {token_acceso}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Error al obtener datos de cauciones: {str(e)}")
        return pd.DataFrame()

def mostrar_curva_cauciones(token_acceso):
    """Muestra la curva de tasas de cauciones"""
    st.subheader("📈 Curva de Tasas de Cauciones")
    
    with st.spinner("Obteniendo datos de cauciones..."):
        df_cauciones = obtener_cauciones(token_acceso)
    
    if df_cauciones.empty:
        st.warning("No se pudieron obtener los datos de cauciones")
        return
    
    # Procesar datos
    df_cauciones['fecha_vencimiento'] = pd.to_datetime(df_cauciones['fechaVencimiento'])
    df_cauciones['dias_plazo'] = (df_cauciones['fecha_vencimiento'] - pd.Timestamp.now()).dt.days
    df_cauciones['tasa_anual'] = df_cauciones['tasa'] * 100  # Convertir a porcentaje
    
    # Ordenar por días de plazo
    df_cauciones = df_cauciones.sort_values('dias_plazo')
    
    # Crear gráfico de curva de rendimiento
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_cauciones['dias_plazo'],
        y=df_cauciones['tasa_anual'],
        mode='lines+markers',
        name='Tasa Anual',
        line=dict(color='royalblue', width=2),
        hovertemplate='Plazo: %{x} días<br>Tasa: %{y:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Curva de Rendimiento de Cauciones',
        xaxis_title='Días al Vencimiento',
        yaxis_title='Tasa Anual (%)',
        hovermode='closest',
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análisis de la curva
    st.subheader("📊 Análisis de la Curva de Cauciones")
    
    if len(df_cauciones) > 1:
        # Calcular pendiente promedio
        pendiente = (df_cauciones['tasa_anual'].iloc[-1] - df_cauciones['tasa_anual'].iloc[0]) / \
                   (df_cauciones['dias_plazo'].iloc[-1] - df_cauciones['dias_plazo'].iloc[0])
        
        if pendiente > 0.01:  # Pendiente positiva significativa
            st.info("🔺 La curva de tasas tiene pendiente positiva, lo que indica que el mercado espera un aumento en las tasas a futuro.")
        elif pendiente < -0.01:  # Pendiente negativa significativa
            st.info("🔻 La curva de tasas tiene pendiente negativa, lo que podría indicar expectativas de bajada de tasas.")
        else:
            st.info("➖ La curva de tasas es relativamente plana, lo que sugiere estabilidad en las expectativas de tasas.")
        
        # Mostrar tasas máximas y mínimas
        max_tasa = df_cauciones['tasa_anual'].max()
        min_tasa = df_cauciones['tasa_anual'].min()
        st.write(f"📊 **Rango de tasas:** {min_tasa:.2f}% - {max_tasa:.2f}%")
    
    # Mostrar tabla con detalles
    st.subheader("📋 Detalle de Cauciones")
    columnas_interes = ['fechaVencimiento', 'dias_plazo', 'tasa_anual', 'moneda']
    st.dataframe(df_cauciones[columnas_interes].rename(columns={
        'fechaVencimiento': 'Vencimiento',
        'dias_plazo': 'Días',
        'tasa_anual': 'Tasa Anual %',
        'moneda': 'Moneda'
    }))

def obtener_tipo_cambio(moneda):
    """
    Obtiene el tipo de cambio actual de la API de IOL.
    
    Args:
        moneda (str): Código de moneda ('usd', 'eur', etc.)
        
    Returns:
        float: Tipo de cambio actual
    """
    try:
        # Valores de ejemplo (reemplazar con llamada real a la API)
        tasas = {
            'usd': 1000.0,
            'eur': 1100.0,
            'brl': 200.0
        }
        return tasas.get(moneda.lower(), 1.0)
    except Exception as e:
        st.error(f"Error al obtener tipo de cambio: {str(e)}")
        return 1000.0  # Valor por defecto en caso de error

def mostrar_tasas_caucion(token_acceso):
    """Muestra las tasas de caución actuales"""
    try:
        response = requests.get(
            "https://api.invertironline.com/api/v2/operaciones/cauciones",
            headers={"Authorization": f"Bearer {token_acceso}"}
        )
        if response.status_code == 200:
            df_tasas = pd.DataFrame(response.json())
            if not df_tasas.empty:
                st.dataframe(df_tasas.head(10))
            else:
                st.error("No se encontraron tasas de caución")
        else:
            st.error("❌ No se pudieron obtener las tasas de caución")
    except Exception as e:
        st.error(f"Error al obtener tasas de caución: {str(e)}")

def optimizar_portafolio(activos, valor_total, n_simulaciones=1000, tasa_libre_riesgo=0.0, comision_rebalanceo=0.01):
    """
    Optimiza la asignación de activos usando simulación de Monte Carlo.
    
    Args:
        activos (dict): Diccionario con datos de activos
        valor_total (float): Valor total del portafolio
        n_simulaciones (int): Número de simulaciones a ejecutar
        tasa_libre_riesgo (float): Tasa libre de riesgo anual
        comision_rebalanceo (float): Comisión por operación de rebalanceo (0-1)
        
    Returns:
        dict: Resultados de la optimización con pesos en ARS/USD y cantidades
    """
    # Inicializar estructura de resultados
    resultados = {
        'asignacion_optima': {},
        'metricas': {
            'retorno_esperado': 0.0,
            'riesgo': 0.0,
            'sharpe': 0.0,
            'valor_esperado_ars': 0.0,
            'valor_esperado_usd': 0.0,
            'valor_esperado_var': 0.0,
            'comision_total': 0.0,
            'comision_porcentaje': 0.0
        },
        'simulaciones': [],
        'moneda_base': 'ARS',
        'comision_total': 0.0,
        'error': None
    }
    
    # Validar entradas
    if not isinstance(activos, dict) or not activos:
        resultados['error'] = "El diccionario de activos está vacío o no es válido"
        return resultados
        
    if valor_total <= 0:
        resultados['error'] = "El valor total del portafolio debe ser mayor a cero"
        return resultados
    
    try:
        # Obtener tipo de cambio actual
        tipo_cambio = obtener_tipo_cambio('usd')
        if tipo_cambio <= 0:
            resultados['error'] = "No se pudo obtener un tipo de cambio válido"
            return resultados
        
        # Procesar activos
        simbolos = []
        precios = []
        monedas = []
        retornos = []
        volatilidades = []
        
        for simbolo, datos in activos.items():
            if not all(k in datos for k in ['precio', 'moneda', 'retorno_medio', 'volatilidad']):
                continue
                
            if not isinstance(datos['precio'], (int, float)) or datos['precio'] <= 0:
                continue
                
            simbolos.append(simbolo)
            precios.append(float(datos['precio']))
            monedas.append(str(datos['moneda']))
            retornos.append(float(datos['retorno_medio']))
            volatilidades.append(float(datos['volatilidad']))
        
        if not simbolos:
            resultados['error'] = "No hay activos válidos para optimizar"
            return resultados
            
        # Convertir a arrays de numpy
        retornos = np.array(retornos)
        volatilidades = np.array(volatilidades)
        precios = np.array(precios)
        
        # Validar dimensiones
        if len(retornos) != len(volatilidades) or len(retornos) != len(precios):
            resultados['error'] = "Inconsistencia en los datos de los activos"
            return resultados
        
        # Generar pesos aleatorios
        np.random.seed(42)  # Para reproducibilidad
        try:
            pesos = np.random.dirichlet(np.ones(len(simbolos)), n_simulaciones)
        except Exception as e:
            resultados['error'] = f"Error al generar pesos aleatorios: {str(e)}"
            return resultados
        
        # Calcular métricas para cada cartera simulada
        simulaciones = []
        for i in range(n_simulaciones):
            try:
                # Calcular retorno y riesgo de la cartera
                retorno_cartera = np.sum(retornos * pesos[i])
                riesgo_cartera = np.sqrt(np.dot(pesos[i].T, np.dot(np.cov(retornos, rowvar=False), pesos[i])))
                
                # Calcular ratio de Sharpe (ajustado por tasa libre de riesgo)
                sharpe_ratio = (retorno_cartera - tasa_libre_riesgo) / (riesgo_cartera + 1e-10)
                
                # Guardar resultados de la simulación
                simulaciones.append({
                    'pesos': pesos[i].copy(),
                    'retorno': float(retorno_cartera),
                    'riesgo': float(riesgo_cartera),
                    'sharpe': float(sharpe_ratio)
                })
            except Exception as e:
                continue  # Continuar con la siguiente simulación si hay un error
        
        if not simulaciones:
            resultados['error'] = "No se pudo completar ninguna simulación válida"
            return resultados
            
        resultados['simulaciones'] = simulaciones
        
        # Encontrar la cartera óptima (máximo ratio de Sharpe)
        mejor_sharpe = max(s['sharpe'] for s in resultados['simulaciones'])
        mejor_cartera = next(s for s in resultados['simulaciones'] if s['sharpe'] == mejor_sharpe)
        
        # Calcular comisiones de rebalanceo y asignación óptima
        comision_total = 0.0
        asignacion_optima = {}
        
        for i, (simbolo, moneda) in enumerate(zip(simbolos, monedas)):
            try:
                peso = float(mejor_cartera['pesos'][i])
                monto_ars = peso * valor_total
                monto_usd = monto_ars / tipo_cambio if moneda == 'USD' else monto_ars / tipo_cambio
                cantidad = monto_ars / precios[i] if moneda == 'ARS' else monto_usd / precios[i]
                comision = monto_ars * comision_rebalanceo
                comision_total += comision
                
                asignacion_optima[simbolo] = {
                    'peso': peso,
                    'monto_ars': float(monto_ars),
                    'monto_usd': float(monto_usd),
                    'cantidad': float(cantidad),
                    'precio': float(precios[i]),
                    'moneda': moneda,
                    'comision_rebalanceo': float(comision)
                }
            except (IndexError, ZeroDivisionError, KeyError) as e:
                continue  # Omitir activos con errores en el cálculo
        
        if not asignacion_optima:
            resultados['error'] = "No se pudo calcular la asignación óptima"
            return resultados
            
        # Actualizar resultados
        resultados['asignacion_optima'] = asignacion_optima
        resultados['comision_total'] = float(comision_total)
        
        # Calcular métricas finales
        resultados['metricas'] = {
            'retorno_esperado': float(mejor_cartera['retorno']),
            'riesgo': float(mejor_cartera['riesgo']),
            'sharpe': float(mejor_sharpe),
            'valor_esperado_ars': float(valor_total * (1 + mejor_cartera['retorno']) - comision_total),
            'valor_esperado_usd': float((valor_total * (1 + mejor_cartera['retorno']) - comision_total) / tipo_cambio),
            'valor_esperado_var': float(valor_total * mejor_cartera['retorno']),
            'comision_total': float(comision_total),
            'comision_porcentaje': float((comision_total / valor_total) * 100) if valor_total > 0 else 0.0
        }
    
    except Exception as e:
        import traceback
        resultados['error'] = f"Error en la optimización del portafolio: {str(e)}\n{traceback.format_exc()}"
    
    return resultados
    
    try:
        # Extraer datos necesarios para la optimización
        simbolos = []
        retornos = []
        volatilidades = []
        pesos = []
        
        for simbolo, datos in activos.items():
            if 'retorno_medio' in datos and 'volatilidad' in datos:
                simbolos.append(simbolo)
                retornos.append(datos['retorno_medio'])
                volatilidades.append(datos['volatilidad'])
                pesos.append(datos['peso'])
        
        if not simbolos:
            return resultados
            
        retornos = np.array(retornos)
        volatilidades = np.array(volatilidades)
        pesos = np.array(pesos)
        
        # Generar correlaciones aleatorias (simplificado)
        n_activos = len(simbolos)
        correlaciones = np.random.uniform(-0.3, 0.9, (n_activos, n_activos))
        np.fill_diagonal(correlaciones, 1.0)
        
        # Calcular matriz de covarianza
        matriz_cov = np.outer(volatilidades, volatilidades) * correlaciones
        
        # Simular carteras
        for _ in range(n_simulaciones):
            # Generar pesos aleatorios
            w = np.random.random(n_activos)
            w = w / np.sum(w)
            
            # Calcular métricas de la cartera
            retorno = np.sum(w * retornos)
            riesgo = np.sqrt(np.dot(w.T, np.dot(matriz_cov, w)))
            sharpe = (retorno - tasa_libre_riesgo) / riesgo if riesgo > 0 else 0
            
            resultados['simulaciones'].append({
                'pesos': w,
                'retorno': retorno,
                'riesgo': riesgo,
                'sharpe': sharpe
            })
        
        # Encontrar cartera óptima (mayor ratio de Sharpe)
        if resultados['simulaciones']:
            mejor_sharpe = max(s['sharpe'] for s in resultados['simulaciones'])
            mejor_cartera = next(s for s in resultados['simulaciones'] if s['sharpe'] == mejor_sharpe)
            
            # Guardar asignación óptima
            for i, simbolo in enumerate(simbolos):
                resultados['asignacion_optima'][simbolo] = {
                    'peso': mejor_cartera['pesos'][i],
                    'monto_ars': mejor_cartera['pesos'][i] * valor_total,
                    'retorno_esperado': retornos[i],
                    'volatilidad': volatilidades[i]
                }
            
            # Guardar métricas de la cartera óptima
            resultados['metricas'] = {
                'retorno_esperado': mejor_cartera['retorno'],
                'riesgo': mejor_cartera['riesgo'],
                'sharpe': mejor_sharpe,
                'valor_esperado_ars': valor_total * (1 + mejor_cartera['retorno']),
                'valor_esperado_usd': (valor_total * (1 + mejor_cartera['retorno'])) / obtener_tipo_cambio('usd'),
                'valor_esperado_var': valor_total * mejor_cartera['retorno']
            }
        
    except Exception as e:
        st.error(f"Error en la optimización: {str(e)}")
    
    return resultados

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.title("🚀 Optimización de Portafolio")
    st.write("""
    Esta herramienta le permite optimizar la distribución de activos en su portafolio 
    considerando comisiones de rebalanceo y mostrando resultados en ARS y USD.
    """)
    
    # Mostrar pestañas para diferentes secciones
    tab1, tab2 = st.tabs(["Optimización", "Análisis de Cauciones"])
    
    with tab1:
        with st.form("optimizacion_form"):
            st.subheader("Configuración de la Optimización")
            
            # Configuración en columnas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                n_simulaciones = st.number_input(
                    "Número de Simulaciones:",
                    min_value=100, max_value=10000, value=1000, step=100,
                    help="Cantidad de carteras aleatorias a generar"
                )
            
            with col2:
                tasa_libre_riesgo = st.number_input(
                    "Tasa Libre de Riesgo Anual (%):",
                    min_value=0.0, max_value=100.0, value=0.0, step=0.1,
                    help="Tasa de referencia para el cálculo del ratio de Sharpe"
                ) / 100  # Convertir a decimal
                
            with col3:
                comision_rebalanceo = st.number_input(
                    "Comisión de Rebalanceo (%):",
                    min_value=0.0, max_value=10.0, value=0.5, step=0.1,
                    help="Comisión por operación de compra/venta"
                ) / 100  # Convertir a decimal
            
            # Sección de estrategias de optimización
            st.subheader("Estrategia de Optimización")
            estrategia = st.selectbox(
                "Seleccione la estrategia:",
                options=['markowitz', 'equi-weight', 'min-variance'],
                format_func=lambda x: {
                    'markowitz': 'Markowitz (Máximo Ratio de Sharpe)',
                    'equi-weight': 'Pesos Iguales',
                    'min-variance': 'Mínima Varianza'
                }[x],
                help="Seleccione el método de optimización a utilizar"
            )
            
            # Mostrar parámetros específicos de la estrategia
            if estrategia == 'markowitz':
                target_return = st.slider(
                    "Retorno Anual Objetivo (%):",
                    min_value=0.0, max_value=100.0, value=15.0, step=0.5,
                    help="Retorno anual objetivo para la optimización"
                ) / 100  # Convertir a decimal
            
            if st.form_submit_button("🚀 Ejecutar Optimización", use_container_width=True):
                with st.spinner("Obteniendo datos del portafolio..."):
                    portafolio = obtener_portafolio(token_acceso, id_cliente)
                
                if not portafolio:
                    st.error("❌ No se pudo obtener el portafolio del cliente")
                    return
                
                activos_raw = portafolio.get('activos', [])
                if not activos_raw:
                    st.warning("⚠️ El portafolio está vacío")
                    return
                
                # Procesar activos para la optimización
                activos_para_optimizacion = {}
                valor_total = 0
                
                for activo in activos_raw:
                    titulo = activo.get('titulo', {})
                    simbolo = titulo.get('simbolo')
                    mercado = titulo.get('mercado')
                    tipo = titulo.get('tipo')
                    cantidad = activo.get('cantidad', 0)
                    precio = activo.get('precioPromedio', 0)
                    moneda = titulo.get('moneda', 'ARS')
                    
                    if simbolo and cantidad > 0 and precio > 0:
                        valor_actual = cantidad * precio
                        valor_total += valor_actual
                        
                        # Usar datos históricos para calcular retorno y volatilidad
                        # (implementar según disponibilidad de datos históricos)
                        retorno_medio = 0.1  # Valor de ejemplo
                        volatilidad = 0.15    # Valor de ejemplo
                        
                        activos_para_optimizacion[simbolo] = {
                            'cantidad': cantidad,
                            'precio': precio,
                            'moneda': moneda,
                            'retorno_medio': retorno_medio,
                            'volatilidad': volatilidad,
                            'valor_actual': valor_actual
                        }
                
                if not activos_para_optimizacion:
                    st.warning("⚠️ No se encontraron activos válidos para optimizar.")
                    return
                
                # Mostrar resumen del portafolio actual
                st.subheader("📊 Portafolio Actual")
                st.write(f"Valor total del portafolio: ${valor_total:,.2f} ARS")
                
                # Ejecutar optimización
                with st.spinner("Optimizando portafolio..."):
                    resultados = optimizar_portafolio(
                        activos_para_optimizacion,
                        valor_total,
                        n_simulaciones=n_simulaciones,
                        tasa_libre_riesgo=tasa_libre_riesgo,
                        comision_rebalanceo=comision_rebalanceo
                    )
                
                # Mostrar resultados
                mostrar_resultados_optimizacion(resultados, valor_total)
    
    # Pestaña de Análisis de Cauciones
    with tab2:
        mostrar_curva_cauciones(token_acceso)

def mostrar_resultados_optimizacion(resultados, valor_inicial):
    """Muestra los resultados de la optimización de portafolio"""
    st.subheader("📈 Resultados de la Optimización")
    
    if not resultados.get('asignacion_optima'):
        st.warning("No se pudo realizar la optimización. Verifique los datos de entrada.")
        return
    
    # Mostrar métricas principales
    metricas = resultados['metricas']
    tipo_cambio = obtener_tipo_cambio('usd')
    
    # Tarjetas con métricas clave
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Retorno Esperado", f"{metricas['retorno_esperado']*100:.2f}%")
    with col2:
        st.metric("Riesgo (Volatilidad)", f"{metricas['riesgo']*100:.2f}%")
    with col3:
        st.metric("Ratio de Sharpe", f"{metricas['sharpe']:.2f}")
    with col4:
        st.metric("Comisión Total", f"${metricas['comision_total']:,.2f} ARS")
    
    # Mostrar valor esperado en ARS y USD
    st.subheader("📊 Valor Esperado del Portafolio")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Valor Esperado (ARS)",
            f"${metricas['valor_esperado_ars']:,.2f}",
            f"{(metricas['valor_esperado_ars']/valor_inicial - 1)*100:.2f}%"
        )
    
    with col2:
        st.metric(
            "Valor Esperado (USD)",
            f"${metricas['valor_esperado_usd']:,.2f}",
            f"{(metricas['valor_esperado_usd']/(valor_inicial/tipo_cambio) - 1)*100:.2f}%"
        )
    
    # Mostrar asignación óptima
    st.subheader("📊 Asignación Óptima de Activos")
    
    # Crear DataFrame para la tabla de asignación
    datos_asignacion = []
    for simbolo, datos in resultados['asignacion_optima'].items():
        datos_asignacion.append({
            'Activo': simbolo,
            'Moneda': datos['moneda'],
            'Peso': f"{datos['peso']*100:.2f}%",
            'Cantidad': f"{datos['cantidad']:,.2f}",
            'Precio': f"${datos['precio']:,.2f}",
            'Monto ARS': f"${datos['monto_ars']:,.2f}",
            'Monto USD': f"${datos['monto_usd']:,.2f}",
            'Comisión': f"${datos['comision_rebalanceo']:,.2f}"
        })
    
    # Mostrar tabla con asignación
    df_asignacion = pd.DataFrame(datos_asignacion)
    st.dataframe(
        df_asignacion,
        column_config={
            'Activo': st.column_config.TextColumn("Activo"),
            'Moneda': st.column_config.TextColumn("Moneda"),
            'Peso': st.column_config.ProgressColumn(
                "Peso",
                format="%.2f%%",
                min_value=0,
                max_value=100,
                width="medium"
            ),
            'Cantidad': st.column_config.NumberColumn("Cantidad", format="%.2f"),
            'Precio': st.column_config.NumberColumn("Precio", format="$%.2f"),
            'Monto ARS': st.column_config.NumberColumn("Monto ARS", format="$%.2f"),
            'Monto USD': st.column_config.NumberColumn("Monto USD", format="$%.2f"),
            'Comisión': st.column_config.NumberColumn("Comisión", format="$%.2f")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Mostrar gráfico de torta de asignación
    st.subheader("📊 Distribución del Portafolio")
    
    fig = go.Figure(data=[go.Pie(
        labels=[f"{k} ({v['moneda']})" for k, v in resultados['asignacion_optima'].items()],
        values=[v['monto_ars'] for v in resultados['asignacion_optima'].values()],
        textinfo='label+percent',
        insidetextorientation='radial',
        hole=0.3
    )])
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar análisis de riesgo-retorno
    st.subheader("📈 Análisis de Riesgo-Retorno")
    
    # Crear gráfico de dispersión de simulaciones
    if 'simulaciones' in resultados and resultados['simulaciones']:
        df_simulaciones = pd.DataFrame([{
            'Riesgo': s['riesgo'] * 100,  # Convertir a porcentaje
            'Retorno': s['retorno'] * 100,  # Convertir a porcentaje
            'Sharpe': s['sharpe']
        } for s in resultados['simulaciones']])
        
        # Ordenar por ratio de Sharpe para mejor visualización
        df_simulaciones = df_simulaciones.sort_values('Sharpe', ascending=False)
        
        # Crear gráfico de dispersión
        fig = px.scatter(
            df_simulaciones,
            x='Riesgo',
            y='Retorno',
            color='Sharpe',
            color_continuous_scale='Viridis',
            labels={
                'Riesgo': 'Riesgo (Desvío Estándar %)',
                'Retorno': 'Retorno Esperado %',
                'Sharpe': 'Ratio de Sharpe'
            },
            title='Frontera Eficiente y Simulaciones de Carteras'
        )
        
        # Agregar línea de frontera eficiente (mejores combinaciones)
        if len(df_simulaciones) > 0:
            # Encontrar carteras eficientes (máximo retorno para cada nivel de riesgo)
            df_eficiente = df_simulaciones.sort_values('Riesgo')
            df_eficiente = df_eficiente.groupby('Riesgo')['Retorno'].max().reset_index()
            
            fig.add_trace(go.Scatter(
                x=df_eficiente['Riesgo'],
                y=df_eficiente['Retorno'],
                mode='lines',
                name='Frontera Eficiente',
                line=dict(color='red', width=2, dash='dash')
            ))
        
        # Agregar punto de cartera óptima
        fig.add_trace(go.Scatter(
            x=[resultados['metricas']['riesgo'] * 100],
            y=[resultados['metricas']['retorno_esperado'] * 100],
            mode='markers',
            name='Cartera Óptima',
            marker=dict(color='red', size=12, symbol='star')
        ))
        
        # Actualizar diseño
        fig.update_layout(
            hovermode='closest',
            coloraxis_colorbar=dict(title='Ratio de Sharpe'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar análisis de sensibilidad
    st.subheader("📊 Análisis de Sensibilidad")
    
    # Calcular métricas de sensibilidad
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Peor Escenario", f"${valor_inicial * (1 - resultados['metricas']['riesgo']):,.2f} ARS")
    with col2:
        st.metric("Escenario Base", f"${valor_inicial:,.2f} ARS")
    with col3:
        st.metric("Mejor Escenario", f"${valor_inicial * (1 + resultados['metricas']['retorno_esperado']):,.2f} ARS")
    
    # Mostrar explicación de resultados
    st.subheader("📝 Interpretación de Resultados")
    
    st.markdown("""
    ### ¿Qué significan estos resultados?
    
    1. **Retorno Esperado**: Es el rendimiento promedio que puede esperar de su portafolio en el próximo período,
       considerando la asignación óptima de activos.
       
    2. **Riesgo (Volatilidad)**: Mide cuánto pueden variar los rendimientos respecto al promedio. 
       Un valor más alto indica mayor incertidumbre en los resultados.
       
    3. **Ratio de Sharpe**: Evalúa el rendimiento ajustado por riesgo. Valores mayores a 1 se consideran buenos,
       y mayores a 2 son excelentes.
       
    4. **Comisión Total**: Costo estimado de rebalancear su portafolio a la asignación óptima.
       
    ### Recomendaciones:
    - Revise la distribución de activos propuesta y asegúrese de que se alinee con su perfil de riesgo.
    - Considere las implicaciones fiscales de las operaciones de rebalanceo.
    - Monitoree periódicamente su portafolio y realice rebalanceos según sea necesario.
    """)
    
    st.info(f"Analizando {len(activos_para_optimizacion)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    # Configuración de optimización extendida
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización:",
            options=['markowitz', 'equi-weight', 'min-variance-l1', 'min-variance-l2', 'long-only'],
            format_func=lambda x: {
                'markowitz': 'Optimización de Markowitz',
                'equi-weight': 'Pesos Iguales',
                'min-variance-l1': 'Mínima Varianza L1',
                'min-variance-l2': 'Mínima Varianza L2',
                'long-only': 'Solo Posiciones Largas'
            }[x]
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, max_value=1.0, value=0.08, step=0.01,
            help="Solo aplica para estrategia Markowitz"
        )
    
    with col3:
        show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)
    
    col1, col2 = st.columns(2)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Crear manager de portafolio con la lista de activos (símbolo y mercado)
                manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                
                # Cargar datos
                if manager_inst.load_data():
                    # Computar optimización
                    use_target = target_return if estrategia == 'markowitz' else None
                    portfolio_result = manager_inst.compute_portfolio(strategy=estrategia, target_return=use_target)
                    
                    if portfolio_result:
                        st.success("✅ Optimización completada")
                        
                        # Mostrar resultados extendidos
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Pesos Optimizados")
                            if portfolio_result.dataframe_allocation is not None:
                                weights_df = portfolio_result.dataframe_allocation.copy()
                                weights_df['Peso (%)'] = weights_df['weights'] * 100
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            metricas = portfolio_result.get_metrics_dict()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Retorno Anual", f"{metricas['Annual Return']:.2%}")
                                st.metric("Volatilidad Anual", f"{metricas['Annual Volatility']:.2%}")
                                st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
                                st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
                            with col_b:
                                st.metric("Skewness", f"{metricas['Skewness']:.4f}")
                                st.metric("Kurtosis", f"{metricas['Kurtosis']:.4f}")
                                st.metric("JB Statistic", f"{metricas['JB Statistic']:.4f}")
                                normalidad = "✅ Normal" if metricas['Is Normal'] else "❌ No Normal"
                                st.metric("Normalidad", normalidad)
                        
                        # Gráfico de distribución de retornos
                        if portfolio_result.returns is not None:
                            st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de pesos
                        if portfolio_result.weights is not None:
                            st.markdown("#### 🥧 Distribución de Pesos")
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=portfolio_result.dataframe_allocation['rics'],
                                values=portfolio_result.weights,
                                textinfo='label+percent',
                                hole=0.4,
                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                            )])
                            fig_pie.update_layout(
                                title="Distribución Optimizada de Activos",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                    else:
                        st.error("❌ Error en la optimización")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    if ejecutar_frontier and show_frontier:
        with st.spinner("Calculando frontera eficiente..."):
            try:
                manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                
                if manager_inst.load_data():
                    portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(
                        target_return=target_return, include_min_variance=True
                    )
                    
                    if portfolios and returns and volatilities:
                        st.success("✅ Frontera eficiente calculada")
                        
                        # Crear gráfico de frontera eficiente
                        fig = go.Figure()
                        
                        # Línea de frontera eficiente
                        fig.add_trace(go.Scatter(
                            x=volatilities, y=returns,
                            mode='lines+markers',
                            name='Frontera Eficiente',
                            line=dict(color='#0d6efd', width=3),
                            marker=dict(size=6)
                        ))
                        
                        # Portafolios especiales
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
                        labels = ['Min Var L1', 'Min Var L2', 'Pesos Iguales', 'Solo Largos', 'Markowitz', 'Markowitz Target']
                        
                        for i, (label, portfolio) in enumerate(portfolios.items()):
                            if portfolio is not None:
                                fig.add_trace(go.Scatter(
                                    x=[portfolio.volatility_annual], 
                                    y=[portfolio.return_annual],
                                    mode='markers',
                                    name=labels[i] if i < len(labels) else label,
                                    marker=dict(size=12, color=colors[i % len(colors)])
                                ))
                        
                        fig.update_layout(
                            title='Frontera Eficiente del Portafolio',
                            xaxis_title='Volatilidad Anual',
                            yaxis_title='Retorno Anual',
                            showlegend=True,
                            template='plotly_white',
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla comparativa de portafolios
                        st.markdown("#### 📊 Comparación de Estrategias")
                        comparison_data = []
                        for label, portfolio in portfolios.items():
                            if portfolio is not None:
                                comparison_data.append({
                                    'Estrategia': label,
                                    'Retorno Anual': f"{portfolio.return_annual:.2%}",
                                    'Volatilidad Anual': f"{portfolio.volatility_annual:.2%}",
                                    'Sharpe Ratio': f"{portfolio.sharpe_ratio:.4f}",
                                    'VaR 95%': f"{portfolio.var_95:.4f}",
                                    'Skewness': f"{portfolio.skewness:.4f}",
                                    'Kurtosis': f"{portfolio.kurtosis:.4f}"
                                })
                        
                        if comparison_data:
                            df_comparison = pd.DataFrame(comparison_data)
                            st.dataframe(df_comparison, use_container_width=True)
                    
                    else:
                        st.error("❌ No se pudo calcular la frontera eficiente")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
    
    # Información adicional extendida
    with st.expander("ℹ️ Información sobre las Estrategias"):
        st.markdown("""
        **Optimización de Markowitz:**
        - Maximiza el ratio de Sharpe (retorno/riesgo)
        - Considera la correlación entre activos
        - Busca la frontera eficiente de riesgo-retorno
        
        **Pesos Iguales:**
        - Distribución uniforme entre todos los activos (1/n)
        - Estrategia simple de diversificación
        - No considera correlaciones históricas
        
        **Mínima Varianza L1:**
        - Minimiza la varianza del portafolio
        - Restricción L1 para regularización (suma de valores absolutos)
        - Tiende a generar portafolios más concentrados
        
        **Mínima Varianza L2:**
        - Minimiza la varianza del portafolio
        - Restricción L2 para regularización (suma de cuadrados)
        - Genera portafolios más diversificados que L1
        
        **Solo Posiciones Largas:**
        - Optimización estándar sin restricciones adicionales
        - Permite solo posiciones compradoras (sin ventas en corto)
        - Suma de pesos = 100%
        
        **Métricas Estadísticas:**
        - **Skewness**: Medida de asimetría de la distribución
        - **Kurtosis**: Medida de la forma de la distribución (colas)
        - **Jarque-Bera**: Test de normalidad de los retornos
        - **VaR 95%**: Valor en riesgo al 95% de confianza
        """)

def mostrar_analisis_tecnico(token_acceso, id_cliente):
    st.markdown("### 📊 Análisis Técnico")
    
    with st.spinner("Obteniendo portafolio..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if not portafolio:
        st.warning("No se pudo obtener el portafolio del cliente")
        return
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("El portafolio está vacío")
        return
    
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos")
        return
    
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos
    )
    
    if simbolo_seleccionado:
        st.info(f"Mostrando gráfico para: {simbolo_seleccionado}")
        
        # Widget de TradingView
        tv_widget = f"""
        <div id="tradingview_{simbolo_seleccionado}" style="height:650px"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "container_id": "tradingview_{simbolo_seleccionado}",
          "width": "100%",
          "height": 650,
          "symbol": "{simbolo_seleccionado}",
          "interval": "D",
          "timezone": "America/Argentina/Buenos_Aires",
          "theme": "light",
          "style": "1",
          "locale": "es",
          "toolbar_bg": "#f4f7f9",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "hide_side_toolbar": false,
          "studies": [
            "MACD@tv-basicstudies",
            "RSI@tv-basicstudies",
            "StochasticRSI@tv-basicstudies",
            "Volume@tv-basicstudies",
            "Moving Average@tv-basicstudies"
          ],
          "drawings_access": {{
            "type": "black",
            "tools": [
              {{"name": "Trend Line"}},
              {{"name": "Horizontal Line"}},
              {{"name": "Fibonacci Retracement"}},
              {{"name": "Rectangle"}},
              {{"name": "Text"}}
            ]
          }},
          "enabled_features": [
            "study_templates",
            "header_indicators",
            "header_compare",
            "header_screenshot",
            "header_fullscreen_button",
            "header_settings",
            "header_symbol_search"
          ]
        }});
        </script>
        """
        components.html(tv_widget, height=680)

def mostrar_movimientos_asesor():
    st.title("👨‍💼 Panel del Asesor")
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.error("Debe iniciar sesión primero")
        return
        
    token_acceso = st.session_state.token_acceso
    
    # Obtener lista de clientes
    clientes = obtener_lista_clientes(token_acceso)
    if not clientes:
        st.warning("No se encontraron clientes")
        return
    
    # Formulario de búsqueda
    with st.form("form_buscar_movimientos"):
        st.subheader("🔍 Buscar Movimientos")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input("Fecha desde", value=date.today() - timedelta(days=30))
        with col2:
            fecha_hasta = st.date_input("Fecha hasta", value=date.today())
        
        # Selección múltiple de clientes
        cliente_opciones = [{"label": f"{c.get('apellidoYNombre', c.get('nombre', 'Cliente'))} ({c.get('numeroCliente', c.get('id', ''))})", 
                           "value": c.get('numeroCliente', c.get('id'))} for c in clientes]
        
        clientes_seleccionados = st.multiselect(
            "Seleccione clientes",
            options=[c['value'] for c in cliente_opciones],
            format_func=lambda x: next((c['label'] for c in cliente_opciones if c['value'] == x), x),
            default=[cliente_opciones[0]['value']] if cliente_opciones else []
        )
        
        # Filtros adicionales
        col1, col2 = st.columns(2)
        with col1:
            tipo_fecha = st.selectbox(
                "Tipo de fecha",
                ["fechaOperacion", "fechaLiquidacion"],
                index=0
            )
            estado = st.selectbox(
                "Estado",
                ["", "Pendiente", "Aprobado", "Rechazado"],
                index=0
            )
        with col2:
            tipo_operacion = st.text_input("Tipo de operación")
            moneda = st.text_input("Moneda", "ARS")
        
        buscar = st.form_submit_button("🔍 Buscar movimientos")
    
    if buscar and clientes_seleccionados:
        with st.spinner("Buscando movimientos..."):
            movimientos = obtener_movimientos_asesor(
                token_portador=token_acceso,
                clientes=clientes_seleccionados,
                fecha_desde=fecha_desde.isoformat(),
                fecha_hasta=fecha_hasta.isoformat(),
                tipo_fecha=tipo_fecha,
                estado=estado or None,
                tipo_operacion=tipo_operacion or None,
                moneda=moneda or None
            )
            
            if movimientos and isinstance(movimientos, list):
                df = pd.DataFrame(movimientos)
                if not df.empty:
                    st.subheader("📋 Resultados de la búsqueda")
                    st.dataframe(df, use_container_width=True)
                    
                    # Mostrar resumen
                    st.subheader("📊 Resumen de Movimientos")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Movimientos", len(df))
                    
                    if 'monto' in df.columns:
                        col2.metric("Monto Total", f"${df['monto'].sum():,.2f}")
                    
                    if 'estado' in df.columns:
                        estados = df['estado'].value_counts().to_dict()
                        col3.metric("Estados", ", ".join([f"{k} ({v})" for k, v in estados.items()]))
                else:
                    st.info("No se encontraron movimientos con los filtros seleccionados")
            else:
                st.warning("No se encontraron movimientos o hubo un error en la consulta")
                if movimientos and not isinstance(movimientos, list):
                    st.json(movimientos)  # Mostrar respuesta cruda para depuración

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No hay cliente seleccionado")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "🔄 Optimización"
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio, token_acceso)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
    
    with tab3:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab4:
        mostrar_cotizaciones_mercado(token_acceso)
    
    with tab5:
        mostrar_optimizacion_portafolio(token_acceso, id_cliente)

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
                    label_visibility="collapsed"
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
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
            elif opcion == "👨\u200d💼 Panel del Asesor":
                mostrar_movimientos_asesor()
                st.info("👆 Seleccione una opción del menú para comenzar")
        else:
            st.info("👆 Ingrese sus credenciales para comenzar")
            
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
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

if __name__ == "__main__":
    main()
