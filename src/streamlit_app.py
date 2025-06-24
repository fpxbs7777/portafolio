import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import yfinance as yf
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
import scipy.optimize as op
from scipy import stats
from fpdf import FPDF

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

def generar_informe_optimizacion(cartera_optima, comision_total, valor_total, tipo_cambio):
    """
    Genera un informe detallado de la optimización del portafolio.
    
    Args:
        cartera_optima (dict): Datos de la cartera óptima
        comision_total (float): Comisión total de rebalanceo
        valor_total (float): Valor total del portafolio
        tipo_cambio (float): Tipo de cambio actual ARS/USD
        
    Returns:
        str: Informe detallado en formato Markdown
    """
    # Calcular métricas clave
    retorno_anual = cartera_optima['retorno'] * 100  # Convertir a porcentaje
    riesgo_anual = cartera_optima['riesgo'] * 100
    sharpe_ratio = cartera_optima['sharpe']
    sortino_ratio = cartera_optima.get('sortino', 0)
    comision_pct = (comision_total / valor_total) * 100
    
    # Generar informe
    informe = f"""## 📊 Análisis de la Optimización

### 📈 Métricas Clave
- **Retorno Anual Esperado:** {retorno_anual:.2f}%
- **Riesgo (Volatilidad Anual):** {riesgo_anual:.2f}%
- **Ratio de Sharpe:** {sharpe_ratio:.2f}
- **Ratio de Sortino:** {sortino_ratio:.2f}
- **Comisión de Rebalanceo:** ${comision_total:,.2f} ARS ({comision_pct:.2f}% del portafolio)
- **Tipo de Cambio:** ${tipo_cambio:,.2f} ARS/USD

### 📝 Recomendaciones
1. **Distribución de Activos:** La cartera óptima sugiere una asignación diversificada entre las diferentes clases de activos.
2. **Comisiones:** Las comisiones de rebalanceo representan un {comision_pct:.2f}% del valor total del portafolio.
3. **Riesgo/Retorno:** El portafolio busca maximizar el retorno ajustado al riesgo según el ratio de Sharpe.

### 🔍 Consideraciones
- Los resultados están basados en datos históricos y no garantizan rendimientos futuros.
- Se recomienda revisar periódicamente la asignación de activos.
- Considere el impacto fiscal de las operaciones de rebalanceo.
"""
    
    return informe

def optimizar_portafolio(activos, valor_total, n_simulaciones=10000, tasa_libre_riesgo=0.0, comision_rebalanceo=0.01):
    """
    Optimiza la asignación de activos usando simulación de Monte Carlo.
    
    Args:
        activos (dict): Diccionario con datos de activos
        valor_total (float): Valor total del portafolio en ARS
        n_simulaciones (int): Número de simulaciones a ejecutar (default: 10000)
        tasa_libre_riesgo (float): Tasa libre de riesgo anual (default: 0.0)
        comision_rebalanceo (float): Comisión por operación de rebalanceo (0-1, default: 0.01)
        
    Returns:
        dict: Resultados de la optimización con pesos en ARS/USD, cantidades y análisis de riesgo
    """
    # Inicializar estructura de resultados
    resultados = {
        'asignacion_optima': {},
        'metricas': {
            'retorno_esperado': 0.0,           # Retorno anual esperado
            'riesgo': 0.0,                     # Volatilidad anual
            'sharpe': 0.0,                     # Ratio de Sharpe
            'sortino': 0.0,                    # Ratio de Sortino
            'valor_esperado_ars': 0.0,         # Valor esperado en ARS (incluye comisiones)
            'valor_esperado_usd': 0.0,         # Valor esperado en USD (incluye comisiones)
            'valor_esperado_var': 0.0,         # Valor en Riesgo (VaR) al 95%
            'comision_total': 0.0,             # Comisión total de rebalanceo
            'comision_porcentaje': 0.0,        # Comisión como porcentaje del portafolio
            'drawdown_maximo': 0.0,            # Drawdown máximo esperado
            'probabilidad_perdida': 0.0,       # Probabilidad de pérdida
            'ratio_ganancia_perdida': 0.0,     # Ratio ganancia/pérdida esperado
            'te': 0.0,                         # Tracking error
            'beta': 0.0,                       # Beta del portafolio
            'alpha': 0.0,                      # Alpha del portafolio
            'informe': ''                      # Informe detallado
        },
        'simulaciones': [],
        'frontera_eficiente': [],
        'moneda_base': 'ARS',
        'comision_total': 0.0,
        'tipo_cambio': 0.0,
        'error': None,
        'advertencias': []
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
            
        resultados['tipo_cambio'] = tipo_cambio
        
        # Procesar activos
        simbolos = []
        precios = []
        monedas = []
        retornos = []
        volatilidades = []
        es_fci = []
        tickers = []
        
        for simbolo, datos in activos.items():
            # Validar campos requeridos
            campos_requeridos = ['precio', 'moneda', 'retorno_medio', 'volatilidad']
            if not all(k in datos for k in campos_requeridos):
                resultados['advertencias'].append(f"El activo {simbolo} no tiene todos los campos requeridos")
                continue
                
            if not isinstance(datos['precio'], (int, float)) or datos['precio'] <= 0:
                resultados['advertencias'].append(f"Precio inválido para {simbolo}")
                continue
                
            # Extraer información del activo
            simbolos.append(simbolo)
            precios.append(float(datos['precio']))
            monedas.append(str(datos['moneda']).upper())
            retornos.append(float(datos['retorno_medio']))
            volatilidades.append(float(datos['volatilidad']))
            es_fci.append(datos.get('es_fci', False))
            tickers.append(datos.get('ticker', simbolo))
        
        if not simbolos:
            resultados['error'] = "No hay activos válidos para optimizar"
            return resultados
            
        # Convertir a arrays de numpy para cálculos eficientes
        retornos = np.array(retornos)
        volatilidades = np.array(volatilidades)
        precios = np.array(precios)
        
        # Calcular matriz de correlación (usando datos históricos si están disponibles)
        try:
            # Si hay datos históricos, calcular correlaciones reales
            if all('retornos_historicos' in activos[s] for s in simbolos):
                retornos_historicos = np.column_stack([activos[s]['retornos_historicos'] for s in simbolos])
                matriz_correlacion = np.corrcoef(retornos_historicos, rowvar=False)
            else:
                # Si no hay datos históricos, usar correlaciones neutrales
                matriz_correlacion = np.eye(len(simbolos))
                for i in range(len(simbolos)):
                    for j in range(i+1, len(simbolos)):
                        # Asignar correlación basada en tipo de activo si está disponible
                        corr = 0.3  # Correlación por defecto
                        if es_fci[i] and es_fci[j]:
                            corr = 0.6  # FCIs tienden a estar más correlacionados
                        elif es_fci[i] or es_fci[j]:
                            corr = 0.1  # FCIs vs otros activos tienen baja correlación
                        matriz_correlacion[i,j] = corr
                        matriz_correlacion[j,i] = corr
        except Exception as e:
            resultados['advertencias'].append(f"Error al calcular correlaciones: {str(e)}")
            matriz_correlacion = np.eye(len(simbolos))
        
        # Generar pesos aleatorios usando el método de Monte Carlo
        np.random.seed(42)  # Para reproducibilidad
        try:
            # Generar pesos con distribución de Dirichlet para asegurar que sumen 1
            pesos = np.random.dirichlet(np.ones(len(simbolos)), n_simulaciones)
            
            # Asegurar que ningún peso sea demasiado pequeño
            pesos = np.maximum(pesos, 1e-6)
            pesos = pesos / pesos.sum(axis=1, keepdims=True)
            
        except Exception as e:
            resultados['error'] = f"Error al generar pesos aleatorios: {str(e)}"
            return resultados
        
        # Calcular métricas para cada cartera simulada
        simulaciones = []
        retornos_simulados = []
        riesgos_simulados = []
        
        for i in range(n_simulaciones):
            try:
                # Calcular retorno esperado de la cartera
                retorno_cartera = np.sum(retornos * pesos[i])
                
                # Calcular riesgo (desviación estándar) de la cartera
                matriz_cov = np.diag(volatilidades) @ matriz_correlacion @ np.diag(volatilidades)
                riesgo_cartera = np.sqrt(np.dot(pesos[i].T, np.dot(matriz_cov, pesos[i])))
                
                # Calcular ratio de Sharpe (ajustado por tasa libre de riesgo)
                sharpe_ratio = (retorno_cartera - tasa_libre_riesgo) / (riesgo_cartera + 1e-10)
                
                # Calcular ratio de Sortino (solo penaliza la volatilidad a la baja)
                retorno_minimo_aceptable = tasa_libre_riesgo / 252  # Tasa diaria
                retornos_por_debajo = np.minimum(0, retornos - retorno_minimo_aceptable)
                riesgo_bajista = np.sqrt(np.dot(pesos[i].T, np.dot(np.diag(volatilidades) @ matriz_correlacion @ np.diag(volatilidades), pesos[i])))
                sortino_ratio = (retorno_cartera - tasa_libre_riesgo) / (riesgo_bajista + 1e-10)
                
                # Guardar resultados de la simulación
                simulacion = {
                    'pesos': pesos[i].copy(),
                    'retorno': float(retorno_cartera),
                    'riesgo': float(riesgo_cartera),
                    'sharpe': float(sharpe_ratio),
                    'sortino': float(sortino_ratio),
                    'pesos_dict': {s: float(w) for s, w in zip(simbolos, pesos[i])}
                }
                
                simulaciones.append(simulacion)
                retornos_simulados.append(retorno_cartera)
                riesgos_simulados.append(riesgo_cartera)
                
            except Exception as e:
                continue  # Continuar con la siguiente simulación si hay un error
        
        if not simulaciones:
            resultados['error'] = "No se pudo completar ninguna simulación válida"
            return resultados
            
        # Ordenar simulaciones por ratio de Sharpe (de mayor a menor)
        simulaciones_ordenadas = sorted(simulaciones, key=lambda x: x['sharpe'], reverse=True)
        resultados['simulaciones'] = simulaciones_ordenadas
        
        # Encontrar la cartera óptima (máximo ratio de Sharpe)
        mejor_cartera = simulaciones_ordenadas[0]
        mejor_sharpe = mejor_cartera['sharpe']
        
        # Calcular frontera eficiente (mejores combinaciones riesgo/retorno)
        if len(simulaciones_ordenadas) > 100:
            # Tomar las 100 mejores carteras para la frontera eficiente
            frontera = []
            paso_riesgo = (max(riesgos_simulados) - min(riesgos_simulados)) / 50
            
            for riesgo_objetivo in np.arange(min(riesgos_simulados), max(riesgos_simulados), paso_riesgo):
                carteras_en_rango = [s for s in simulaciones_ordenadas 
                                   if abs(s['riesgo'] - riesgo_objetivo) < paso_riesgo]
                if carteras_en_rango:
                    mejor_en_rango = max(carteras_en_rango, key=lambda x: x['retorno'])
                    frontera.append(mejor_en_rango)
            
            resultados['frontera_eficiente'] = frontera[:100]  # Limitar a 100 puntos
        
        # Calcular comisiones de rebalanceo y asignación óptima
        comision_total = 0.0
        asignacion_optima = {}
        
        # Calcular valor actual de cada activo en el portafolio actual
        valor_actual_por_activo = {}
        for i, simbolo in enumerate(simbolos):
            valor_actual = precios[i] * (activos[simbolo].get('cantidad', 0))
            if monedas[i] == 'USD':
                valor_actual *= tipo_cambio
            valor_actual_por_activo[simbolo] = valor_actual
        
        valor_total_actual = sum(valor_actual_por_activo.values())
        
        for i, (simbolo, moneda, es_f) in enumerate(zip(simbolos, monedas, es_fci)):
            try:
                peso = float(mejor_cartera['pesos'][i])
                monto_objetivo_ars = peso * valor_total
                
                # Calcular monto actual en ARS
                monto_actual_ars = valor_actual_por_activo.get(simbolo, 0)
                
                # Calcular diferencia y comisión
                diferencia = abs(monto_objetivo_ars - monto_actual_ars)
                comision = diferencia * comision_rebalanceo
                
                # Si es FCI, ajustar comisión según el plazo
                if es_f:
                    # Ejemplo: comisión reducida para FCIs a 30 días o más
                    plazo_dias = activos[simbolo].get('plazo_dias', 1)
                    if plazo_dias >= 30:
                        comision *= 0.5  # 50% de descuento en comisión
                
                comision_total += comision
                
                # Calcular cantidades y montos
                precio_ars = precios[i] * (tipo_cambio if moneda == 'USD' else 1)
                cantidad_objetivo = monto_objetivo_ars / precio_ars
                
                # Calcular variación porcentual
                variacion_pct = ((monto_objetivo_ars - monto_actual_ars) / (monto_actual_ars + 1e-10)) * 100
                
                # Calcular rendimiento esperado en ARS y USD
                rendimiento_anual_ars = retornos[i] * monto_objetivo_ars
                rendimiento_anual_usd = rendimiento_anual_ars / tipo_cambio
                
                # Guardar asignación óptima con toda la información
                asignacion_optima[simbolo] = {
                    'peso': peso,
                    'monto_ars': monto_objetivo_ars,
                    'monto_anterior_ars': monto_actual_ars,
                    'monto_usd': monto_objetivo_ars / tipo_cambio,
                    'cantidad': cantidad_objetivo,
                    'precio': precios[i],
                    'moneda': moneda,
                    'comision_rebalanceo': comision,
                    'variacion_pct': variacion_pct,
                    'rendimiento_anual_ars': rendimiento_anual_ars,
                    'rendimiento_anual_usd': rendimiento_anual_usd,
                    'ticker': tickers[i],
                    'es_fci': es_f,
                    'volatilidad': volatilidades[i],
                    'retorno_esperado': retornos[i]
                }
                
            except (IndexError, ZeroDivisionError, KeyError) as e:
                resultados['advertencias'].append(f"Error al procesar {simbolo}: {str(e)}")
                continue
        
        if not asignacion_optima:
            resultados['error'] = "No se pudo calcular la asignación óptima"
            return resultados
        
        # Calcular métricas de riesgo avanzadas
        retornos_simulados = np.array([s['retorno'] for s in simulaciones_ordenados])
        riesgos_simulados = np.array([s['riesgo'] for s in simulaciones_ordenados])
        
        # Valor en Riesgo (VaR) al 95%
        var_95 = np.percentile([s['retorno'] for s in simulaciones_ordenados], 5)
        
        # Drawdown máximo
        drawdown_max = min([s['retorno'] - max(retornos_simulados[:i+1]) for i, s in enumerate(simulaciones_ordenados)])
        
        # Probabilidad de pérdida
        prob_perdida = len([r for r in retornos_simulados if r < 0]) / len(retornos_simulados)
        
        # Ratio ganancia/pérdida
        ganancias = [r for r in retornos_simulados if r > 0]
        perdidas = [r for r in retornos_simulados if r < 0]
        ratio_ganancia_perdida = (sum(ganancias)/len(ganancias)) / abs(sum(perdidas)/len(perdidas)) if ganancias and perdidas else 0
        
        # Actualizar resultados
        resultados['asignacion_optima'] = asignacion_optima
        resultados['comision_total'] = comision_total
        
        # Calcular métricas finales
        resultados['metricas'] = {
            'retorno_esperado': mejor_cartera['retorno'],
            'riesgo': mejor_cartera['riesgo'],
            'sharpe': mejor_cartera['sharpe'],
            'sortino': mejor_cartera['sortino'],
            'valor_esperado_ars': valor_total * (1 + mejor_cartera['retorno']) - comision_total,
            'valor_esperado_usd': (valor_total * (1 + mejor_cartera['retorno']) - comision_total) / tipo_cambio,
            'valor_esperado_var': var_95,
            'comision_total': comision_total,
            'comision_porcentaje': (comision_total / valor_total) * 100 if valor_total > 0 else 0.0,
            'drawdown_maximo': drawdown_max,
            'probabilidad_perdida': prob_perdida,
            'ratio_ganancia_perdida': ratio_ganancia_perdida,
            'te': np.std([s['retorno'] - mejor_cartera['retorno'] for s in simulaciones_ordenados]),
            'beta': 1.0,  # Se asume 1 como valor por defecto, se puede ajustar con benchmark
            'alpha': mejor_cartera['retorno'] - (tasa_libre_riesgo + 1.0 * (mejor_cartera['retorno'] - tasa_libre_riesgo)),
            'informe': generar_informe_optimizacion(mejor_cartera, comision_total, valor_total, tipo_cambio)
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

def generar_reporte_descargable(resultados, valor_inicial):
    """
    Genera un informe PDF descargable con los resultados de la optimización.
    
    Args:
        resultados (dict): Resultados de la optimización
        valor_inicial (float): Valor inicial del portafolio
        
    Returns:
        bytes: Contenido del PDF generado
    """
    try:
        from fpdf import FPDF
        import io
        from datetime import datetime
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Configuración de fuente
        pdf.set_font('Arial', 'B', 16)
        
        # Título
        pdf.cell(0, 10, 'Informe de Optimización de Portafolio', 0, 1, 'C')
        pdf.ln(5)
        
        # Fecha
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        pdf.ln(10)
        
        # Sección de métricas clave
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Métricas Clave', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Tabla de métricas
        col_width = pdf.w / 2.5
        row_height = 8
        
        # Encabezados
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(col_width, row_height, 'Métrica', 1, 0, 'C', True)
        pdf.cell(col_width, row_height, 'Valor', 1, 1, 'C', True)
        
        # Filas
        pdf.cell(col_width, row_height, 'Retorno Anual Esperado', 1)
        pdf.cell(col_width, row_height, f"{resultados['metricas']['retorno_esperado']*100:.2f}%", 1, 1)
        
        pdf.cell(col_width, row_height, 'Riesgo (Volatilidad)', 1)
        pdf.cell(col_width, row_height, f"{resultados['metricas']['riesgo']*100:.2f}%", 1, 1)
        
        pdf.cell(col_width, row_height, 'Ratio de Sharpe', 1)
        pdf.cell(col_width, row_height, f"{resultados['metricas']['sharpe']:.2f}", 1, 1)
        
        pdf.cell(col_width, row_height, 'Valor Esperado (ARS)', 1)
        pdf.cell(col_width, row_height, f"${resultados['metricas']['valor_esperado_ars']:,.2f}", 1, 1)
        
        pdf.cell(col_width, row_height, 'Comisión Total', 1)
        pdf.cell(col_width, row_height, f"${resultados['comision_total']:,.2f}", 1, 1)
        
        # Sección de asignación de activos
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Asignación de Activos', 0, 1)
        
        # Tabla de asignación
        col_widths = [60, 25, 25, 25, 30, 30]  # Ajustar según necesidad
        headers = ['Activo', 'Moneda', 'Peso (%)', 'Cantidad', 'Monto (ARS)', 'Comisión']
        
        # Encabezados de la tabla
        pdf.set_fill_color(200, 220, 255)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
        pdf.ln()
        
        # Filas de datos
        pdf.set_font('Arial', '', 8)
        for simbolo, datos in resultados['asignacion_optima'].items():
            pdf.cell(col_widths[0], 8, simbolo[:15], 1)
            pdf.cell(col_widths[1], 8, datos['moneda'], 1, 0, 'C')
            pdf.cell(col_widths[2], 8, f"{datos['peso']*100:.2f}%", 1, 0, 'R')
            pdf.cell(col_widths[3], 8, f"{datos['cantidad']:,.2f}", 1, 0, 'R')
            pdf.cell(col_widths[4], 8, f"${datos['monto_ars']:,.2f}", 1, 0, 'R')
            pdf.cell(col_widths[5], 8, f"${datos['comision_rebalanceo']:,.2f}", 1, 1, 'R')
        
        # Pie de página
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, 'Informe generado automáticamente por el sistema de optimización de portafolio', 0, 1, 'C')
        
        # Guardar PDF en un buffer
        buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S')
        buffer.write(pdf_bytes.encode('latin-1'))
        
        # Devolver el contenido del buffer
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error al generar el informe: {str(e)}")
        return None

def mostrar_resultados_optimizacion(resultados, valor_inicial):
    """
    Muestra los resultados detallados de la optimización de portafolio con visualizaciones interactivas.
    
    Args:
        resultados (dict): Resultados de la función optimizar_portafolio
        valor_inicial (float): Valor inicial del portafolio
    """
    if 'error' in resultados and resultados['error']:
        st.error(f"❌ Error en la optimización: {resultados['error']}")
        if 'advertencias' in resultados and resultados['advertencias']:
            with st.expander("⚠️ Advertencias"):
                for advertencia in resultados['advertencias']:
                    st.warning(advertencia)
        return
    
    if not resultados.get('asignacion_optima'):
        st.warning("⚠️ No se encontró una asignación óptima")
        return
    
    # Obtener tipo de cambio para mostrar valores en USD
    tipo_cambio = resultados.get('tipo_cambio', 1.0)
    
    # Mostrar encabezado con métricas clave
    st.markdown("## 📊 Resultados de la Optimización de Portafolio")

    # Tarjetas con métricas clave
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Retorno Esperado", f"{resultados['metricas']['retorno_esperado']*100:.2f}%")
    with col2:
        st.metric("📉 Riesgo (Volatilidad)", 
                 f"{resultados['metricas']['riesgo']*100:.2f}%",
                 help="Desviación estándar anualizada de los retornos")
    with col3:
        st.metric("📊 Ratio de Sharpe", 
                 f"{resultados['metricas']['sharpe']:.2f}",
                 help="Retorno ajustado al riesgo (mayor es mejor)")
    with col4:
        st.metric("💰 Valor Esperado (ARS)", 
                 f"${resultados['metricas']['valor_esperado_ars']:,.2f}",
                 help=f"Valor esperado del portafolio (inversión inicial: ${valor_inicial:,.2f})")
    
    # Pestañas para organizar la información
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Resumen", "📊 Análisis", "📈 Gráficos", "📝 Informe Detallado"])
    
    with tab1:  # Pestaña de Resumen
        st.subheader("📋 Resumen de la Asignación Óptima")
        
        # Crear DataFrame para la asignación con más detalles
        asignacion_data = []
        for simbolo, datos in resultados['asignacion_optima'].items():
            asignacion_data.append({
                'Activo': simbolo,
                'Ticker': datos.get('ticker', simbolo),
                'Moneda': datos['moneda'],
                'Peso (%)': datos['peso'] * 100,
                'Monto (ARS)': datos['monto_ars'],
                'Monto (USD)': datos['monto_usd'],
                'Cantidad': datos['cantidad'],
                'Precio': datos['precio'],
                'Comisión (ARS)': datos['comision_rebalanceo'],
                'Variación (%)': datos['variacion_pct'],
                'Retorno Anual (%)': datos['retorno_esperado'] * 100,
                'Volatilidad (%)': datos['volatilidad'] * 100,
                'Tipo': 'FCI' if datos.get('es_fci', False) else 'Otro'
            })
        
        df_asignacion = pd.DataFrame(asignacion_data)
        
        # Mostrar KPI resumen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💼 Número de Activos", len(df_asignacion))
        with col2:
            st.metric("💵 Comisión Total", f"${resultados['comision_total']:,.2f} ARS")
        with col3:
            st.metric("🔄 Rotación", f"{sum(abs(df_asignacion['Variación (%)']) > 0.1):.0f} activos con cambios > 0.1%")
        
        # Mostrar tabla con asignación
        st.dataframe(
            df_asignacion[['Activo', 'Ticker', 'Moneda', 'Peso (%)', 'Monto (ARS)', 'Cantidad', 'Comisión (ARS)']]
            .sort_values('Peso (%)', ascending=False)
            .style.format({
                'Peso (%)': '{:.2f}%',
                'Monto (ARS)': '${:,.2f}',
                'Cantidad': '{:,.4f}',
                'Comisión (ARS)': '${:,.2f}'
            }),
            height=400
        )
        
        # Mostrar gráfico de torta por moneda
        st.subheader("🌍 Distribución por Moneda")
        df_monedas = df_asignacion.groupby('Moneda')['Monto (ARS)'].sum().reset_index()
        fig_monedas = px.pie(
            df_monedas, 
            values='Monto (ARS)', 
            names='Moneda',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_monedas, use_container_width=True)
    
    with tab2:  # Pestaña de Análisis
        st.subheader("📊 Análisis de Riesgo y Retorno")
        
        # Mostrar métricas de riesgo
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📉 Valor en Riesgo (VaR 95%)", 
                     f"{resultados['metricas']['valor_esperado_var']*100:.2f}%",
                     help="Pérdida máxima esperada en el peor 5% de los escenarios")
            st.metric("📊 Drawdown Máximo", 
                     f"{resultados['metricas']['drawdown_maximo']*100:.2f}%",
                     help="Máxima caída desde el pico histórico")
            st.metric("📈 Ratio de Sortino", 
                     f"{resultados['metricas'].get('sortino', 0):.2f}",
                     help="Retorno ajustado por riesgo a la baja (mayor es mejor)")
        
        with col2:
            st.metric("📊 Probabilidad de Pérdida", 
                     f"{resultados['metricas']['probabilidad_perdida']*100:.2f}%",
                     help="Probabilidad de obtener un retorno negativo")
            st.metric("📈 Ratio Ganancia/Pérdida", 
                     f"{resultados['metricas']['ratio_ganancia_perdida']:.2f}",
                     help="Relación entre ganancias y pérdidas esperadas")
            st.metric("📊 Tracking Error", 
                     f"{resultados['metricas'].get('te', 0)*100:.2f}%",
                     help="Desviación estándar de la diferencia de retornos vs benchmark")
        
        # Mostrar matriz de correlación
        st.subheader("🔄 Matriz de Correlación")
        activos = list(resultados['asignacion_optima'].keys())
        n_activos = len(activos)
        
        if n_activos > 1:
            # Crear matriz de correlación (ejemplo simplificado)
            correlaciones = np.eye(n_activos)
            for i in range(n_activos):
                for j in range(i+1, n_activos):
                    # Simular correlación basada en tipos de activos
                    if (resultados['asignacion_optima'][activos[i]]['es_fci'] and 
                        resultados['asignacion_optima'][activos[j]]['es_fci']):
                        corr = 0.6  # FCIs correlacionados
                    else:
                        corr = np.random.uniform(-0.2, 0.4)  # Baja correlación
                    correlaciones[i,j] = corr
                    correlaciones[j,i] = corr
            
            # Crear heatmap
            fig_corr = px.imshow(
                correlaciones,
                x=activos,
                y=activos,
                color_continuous_scale='RdBu',
                zmin=-1,
                zmax=1,
                title='Correlación entre Activos'
            )
            fig_corr.update_layout(width=800, height=700)
            st.plotly_chart(fig_corr, use_container_width=True)
    
    with tab3:  # Pestaña de Gráficos
        st.subheader("📈 Visualización de la Cartera Óptima")
        
        # Gráfico de torta por activo
        st.subheader("📊 Distribución por Activo")
        df_activos = pd.DataFrame([{
            'Activo': k, 
            'Monto (ARS)': v['monto_ars'],
            'Peso (%)': v['peso'] * 100,
            'Moneda': v['moneda']
        } for k, v in resultados['asignacion_optima'].items()])
        
        fig_pie = px.pie(
            df_activos, 
            values='Monto (ARS)', 
            names='Activo',
            hover_data=['Moneda', 'Peso (%)'],
            hole=0.4,
            title='Distribución del Portafolio por Activo',
            color_discrete_sequence=px.colors.sequential.Plasma
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Frontera eficiente
        if 'frontera_eficiente' in resultados and resultados['frontera_eficiente']:
            st.subheader("📉 Frontera Eficiente")
            
            # Preparar datos para el gráfico
            frontera = resultados['frontera_eficiente']
            df_frontera = pd.DataFrame([{
                'Riesgo': s['riesgo'],
                'Retorno': s['retorno'],
                'Sharpe': s['sharpe']
            } for s in frontera])
            
            # Punto óptimo
            punto_optimo = {
                'Riesgo': [resultados['metricas']['riesgo']],
                'Retorno': [resultados['metricas']['retorno_esperado']],
                'Label': ['Portafolio Óptimo']
            }
            
            # Crear gráfico de dispersión
            fig = px.scatter(
                df_frontera, 
                x='Riesgo', 
                y='Retorno',
                color='Sharpe',
                title='Frontera Eficiente',
                labels={
                    'Riesgo': 'Riesgo (Desviación Estándar Anualizada)', 
                    'Retorno': 'Retorno Anual Esperado'
                },
                color_continuous_scale='Viridis',
                hover_data=['Sharpe']
            )
            
            # Agregar punto óptimo
            fig.add_scatter(
                x=punto_optimo['Riesgo'],
                y=punto_optimo['Retorno'],
                mode='markers+text',
                marker=dict(color='red', size=12, line=dict(color='white', width=2)),
                text=punto_optimo['Label'],
                textposition='top center',
                name='Portafolio Óptimo',
                hovertemplate=(
                    '<b>Portafolio Óptimo</b><br>' +
                    'Riesgo: %{x:.2%}<br>' +
                    'Retorno: %{y:.2%}<br>' +
                    'Sharpe: ' + f"{resultados['metricas']['sharpe']:.2f}<br>"
                )
            )
            
            # Personalizar formato de ejes
            fig.update_layout(
                xaxis_tickformat=".0%",
                yaxis_tickformat=".0%",
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:  # Pestaña de Informe Detallado
        st.subheader("📝 Informe de Optimización")
        
        # Mostrar informe generado
        if 'informe' in resultados['metricas']:
            st.markdown(resultados['metricas']['informe'])
        
        # Análisis de sensibilidad
        st.subheader("📊 Análisis de Sensibilidad")
        
        # Simular diferentes escenarios
        escenarios = [
            ('Pesimista', 0.8, '🔴'),
            ('Base', 1.0, '🟡'),
            ('Optimista', 1.2, '🟢')
        ]
        
        for nombre, factor, emoji in escenarios:
            with st.expander(f"{emoji} Escenario {nombre}"):
                col1, col2, col3 = st.columns(3)
                retorno_ajustado = resultados['metricas']['retorno_esperado'] * factor
                riesgo_ajustado = resultados['metricas']['riesgo'] * (1.5 - factor/2)  # Menor riesgo en escenarios optimistas
                
                with col1:
                    st.metric("Retorno Esperado", f"{retorno_ajustado*100:.2f}%")
                with col2:
                    st.metric("Riesgo", f"{riesgo_ajustado*100:.2f}%")
                with col3:
                    valor_esperado = valor_inicial * (1 + retorno_ajustado) - resultados['comision_total']
                    st.metric("Valor Esperado (ARS)", f"${valor_esperado:,.2f}", 
                             delta=f"${(valor_esperado - valor_inicial):,.2f}")
        
        # Recomendaciones de acción
        st.subheader("🎯 Recomendaciones")
        st.markdown("""
        1. **Rebalanceo Inmediato**: Ajuste su cartera según la asignación óptima mostrada.
        2. **Monitoreo Mensual**: Revise la asignación al menos una vez al mes.
        3. **Consideraciones Fiscales**: Consulte con un contador sobre las implicaciones fiscales del rebalanceo.
        4. **Diversificación**: Considere agregar activos de baja correlación para reducir el riesgo.
        """)
        
        # Descargar informe
        st.download_button(
            label="📥 Descargar Informe Completo",
            data=generar_reporte_descargable(resultados, valor_inicial),
            file_name=f"informe_optimizacion_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        
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

def obtener_tokens(usuario, contraseña):
    """
    Obtiene los tokens de acceso y refresh de la API de IOL.
    
    Args:
        usuario (str): Nombre de usuario de IOL
        contraseña (str): Contraseña de IOL
        
    Returns:
        tuple: (token_acceso, refresh_token) o (None, None) en caso de error
    """
    try:
        # URL de autenticación de IOL
        url = "https://api.invertironline.com/token"
        
        # Datos para la autenticación
        data = {
            'username': usuario,
            'password': contraseña,
            'grant_type': 'password'
        }
        
        # Headers requeridos
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Realizar la petición POST
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()  # Lanza error para códigos 4XX/5XX
        
        # Extraer tokens de la respuesta
        datos_respuesta = response.json()
        token_acceso = datos_respuesta.get('access_token')
        refresh_token = datos_respuesta.get('refresh_token')
        
        if not token_acceso or not refresh_token:
            raise ValueError("No se pudieron obtener los tokens de la respuesta")
            
        return token_acceso, refresh_token
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión con IOL: {str(e)}")
        return None, None
    except Exception as e:
        st.error(f"Error al obtener tokens: {str(e)}")
        return None, None

def verificar_token(token_acceso):
    """
    Verifica si un token de acceso es válido.
    
    Args:
        token_acceso (str): Token de acceso a verificar
        
    Returns:
        bool: True si el token es válido, False en caso contrario
    """
    try:
        url = "https://api.invertironline.com/api/v2/estadocuenta"
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except:
        return False

def refrescar_token(refresh_token):
    """
    Obtiene un nuevo token de acceso usando el refresh token.
    
    Args:
        refresh_token (str): Refresh token para obtener un nuevo access token
        
    Returns:
        str: Nuevo token de acceso o None en caso de error
    """
    try:
        url = "https://api.invertironline.com/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json().get('access_token')
    except:
        return None

def obtener_lista_clientes(token_acceso):
    """
    Obtiene la lista de clientes asociados a la cuenta del asesor.
    
    Args:
        token_acceso (str): Token de acceso de la API de IOL
        
    Returns:
        list: Lista de diccionarios con información de los clientes
    """
    try:
        url = "https://api.invertironline.com/api/v2/usuarios/me"
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Esto lanzará un error para códigos 4XX/5XX
        
        data = response.json()
        
        # Si el usuario tiene múltiples cuentas, devolver la lista de cuentas
        if 'cuentas' in data and data['cuentas']:
            return data['cuentas']
        
        # Si no hay cuentas pero hay datos de usuario, devolver la cuenta principal
        if 'usuario' in data and data['usuario']:
            return [{
                'id': data['usuario'].get('id'),
                'numeroCliente': data['usuario'].get('numeroCliente'),
                'apellidoYNombre': data['usuario'].get('apellidoYNombre', 'Cliente')
            }]
            
        # Si no hay datos de usuario, intentar con la respuesta directa
        if 'id' in data:
            return [{
                'id': data.get('id'),
                'numeroCliente': data.get('numeroCliente'),
                'apellidoYNombre': data.get('apellidoYNombre', 'Cliente')
            }]
            
        return []
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Error HTTP al obtener clientes: {e.response.status_code}"
        if e.response.text:
            error_msg += f" - {e.response.text}"
        st.error(error_msg)
        # Si el error es 401 (No autorizado), forzar cierre de sesión
        if e.response.status_code == 401 and 'token_acceso' in st.session_state:
            del st.session_state.token_acceso
            st.rerun()
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener clientes: {str(e)}")
    except Exception as e:
        st.error(f"Error inesperado al obtener clientes: {str(e)}")
    
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
                            # Seleccionar el primer cliente por defecto si no hay ninguno seleccionado
                            if not st.session_state.cliente_seleccionado:
                                st.session_state.cliente_seleccionado = clientes[0]
                            st.rerun()  # Forzar actualización de la interfaz
                        else:
                            st.warning("No se encontraron clientes. Verifique que su cuenta tenga los permisos necesarios.")
                    except Exception as e:
                        st.error(f"Error al cargar clientes: {str(e)}")
                        # Si hay un error al cargar clientes, limpiar el estado para evitar bucles
                        st.session_state.clientes = []
                        st.session_state.cliente_seleccionado = None
            
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
