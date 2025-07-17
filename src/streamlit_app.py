import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import numpy as np
from dateutil.parser import parse
import re
import unicodedata
import bs4
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Configuración de la página
st.set_page_config(page_title="Cotizaciones IOL", layout="wide")
st.markdown("# Cotizaciones de instrumentos argentinos (IOL)")

urls = {
    "Bonos": "https://iol.invertironline.com/mercado/cotizaciones/argentina/bonos/todos",
    "Letras": "https://iol.invertironline.com/mercado/cotizaciones/argentina/letras/todas",
    "Obligaciones Negociables": "https://iol.invertironline.com/mercado/cotizaciones/argentina/obligaciones-negociables/todos",
    "Cauciones": "https://iol.invertironline.com/mercado/cotizaciones/argentina/cauciones/todas"
}

# Base de datos de instrumentos financieros argentinos
INSTRUMENTOS_FINANCIEROS = {
    # BONCER - Soberanos en pesos más CER
    "BONCER2026": {
        "nombre": "BONCER 2% $ 2026",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "2,00%",
        "vencimiento": "09-nov-26",
        "tipo": "BONCER",
        "moneda": "PESOS",
        "ajuste": "CER",
        "categoria_scraping": "Soberanos en pesos más Cer",
        "decreto": "676/2020"
    },
    "BONCER2028": {
        "nombre": "BONCER 2.25% $ 2028", 
        "fecha_emision": "04-sep-20",
        "tasa_interes": "2,25%",
        "vencimiento": "09-nov-28",
        "tipo": "BONCER",
        "moneda": "PESOS",
        "ajuste": "CER",
        "categoria_scraping": "Soberanos en pesos más Cer",
        "decreto": "676/2020"
    },
    "BONCER2025": {
        "nombre": "BONOS DEL TESORO NACIONAL EN PESOS CON AJUSTE POR C.E.R. 1,80 % VTO. 9 de Noviembre de 2025",
        "fecha_emision": "23-may-22",
        "tasa_interes": "1,80%",
        "vencimiento": "09-nov-25",
        "tipo": "BONCER",
        "moneda": "PESOS",
        "ajuste": "CER",
        "categoria_scraping": "Soberanos en pesos más Cer",
        "decreto": "Nacional"
    },
    "BONCER2031": {
        "nombre": "BONOS DEL TESORO NACIONAL EN PESOS CON AJUSTE POR C.E.R. 2,5 % VTO. 30 de Noviembre de 2031",
        "fecha_emision": "31-may-22",
        "tasa_interes": "2,50%",
        "vencimiento": "30-nov-31",
        "tipo": "BONCER",
        "moneda": "PESOS",
        "ajuste": "CER",
        "categoria_scraping": "Soberanos en pesos más Cer",
        "decreto": "Nacional"
    },
    "BONCER2025AGO": {
        "nombre": "BONOS DEL TESORO NACIONAL EN PESOS CON AJUSTE POR C.E.R. VTO. 23 de Agosto de 2025",
        "fecha_emision": "23-may-23",
        "tasa_interes": "0,00%",
        "vencimiento": "23-ago-25",
        "tipo": "BONCER",
        "moneda": "PESOS",
        "ajuste": "CER",
        "categoria_scraping": "Soberanos en pesos más Cer",
        "decreto": "Nacional"
    },
    "BONCER2025JUN": {
        "nombre": "BONOS DEL TESORO NACIONAL EN PESOS CON AJUSTE POR C.E.R. 4,5 % VTO. 18 de Junio de 2025",
        "fecha_emision": "31-may-23",
        "tasa_interes": "4,50%",
        "vencimiento": "18-jun-25",
        "tipo": "BONCER",
        "moneda": "PESOS",
        "ajuste": "CER",
        "categoria_scraping": "Soberanos en pesos más Cer",
        "decreto": "Nacional"
    },
    
    # BONOS STEP UP USD - Soberanos en dólares
    "AE30D": {
        "nombre": "BONO GLOBAL REP. ARGENTINA USD STEP UP 2030",
        "fecha_emision": "04-sep-20", 
        "tasa_interes": "0,125% - 0,50% - 0,75% - 1,75%",
        "vencimiento": "09-jul-30",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AE35D": {
        "nombre": "BONO GLOBAL REP. ARGENTINA USD STEP UP 2035",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 1,125% - 1,50% - 3,625% - 4,125% - 4,75%- 5%",
        "vencimiento": "09-jul-35", 
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AE38D": {
        "nombre": "BONO GLOBAL REP. ARGENTINA USD STEP UP 2038",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 2% - 3,875% -  4,25%  - 5%",
        "vencimiento": "09-ene-38",
        "tipo": "STEP_UP", 
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AE41D": {
        "nombre": "BONO GLOBAL REP. ARGENTINA USD STEP UP 2041",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 2,5% - 3,8% -  4,875%",
        "vencimiento": "09-jul-41",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AE46D": {
        "nombre": "BONO GLOBAL REP. ARGENTINA USD STEP UP 2046", 
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 1,125% -1,5% - 3,625% - 4,125% - 4,375% - 5%",
        "vencimiento": "09-jul-46",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AE29D": {
        "nombre": "BONO GLOBAL REP ARGENTINA USD 1% 2029",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "1,000%",
        "vencimiento": "09-jul-29",
        "tipo": "TASA_FIJA",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    
    # BONOS STEP UP EUR - Soberanos en euros
    "AE30E": {
        "nombre": "BONO GLOBAL REP. ARGENTINA EUR STEP UP 2030",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125%",
        "vencimiento": "09-jul-30",
        "tipo": "STEP_UP",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "676/2020"
    },
    "AE35E": {
        "nombre": "BONO GLOBAL REP. ARGENTINA EUR STEP UP 2035",
        "fecha_emision": "04-sep-20", 
        "tasa_interes": "0,125% - 0,75% - 0,875% -  2,5% - 3,875% - 4%",
        "vencimiento": "09-jul-35",
        "tipo": "STEP_UP",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "676/2020"
    },
    "AE38E": {
        "nombre": "BONO GLOBAL REP. ARGENTINA EUR STEP UP 2038",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 1,5% - 3% -  3,75% - 4,25%",
        "vencimiento": "09-ene-38",
        "tipo": "STEP_UP",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "676/2020"
    },
    "AE41E": {
        "nombre": "BONO GLOBAL REP. ARGENTINA EUR STEP UP 2041",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 1,5% - 3% -  4,5%",
        "vencimiento": "09-jul-41",
        "tipo": "STEP_UP",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "676/2020"
    },
    "AE46E": {
        "nombre": "BONO GLOBAL REP. ARGENTINA EUR STEP UP 2046",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 0,75% - 0,875% -  2,5% - 3,875% - 4% - 4,125%",
        "vencimiento": "09-jul-46",
        "tipo": "STEP_UP",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "676/2020"
    },
    "AE29E": {
        "nombre": "BONO GLOBAL REP. ARGENTINA EUR 0,50 % 2029",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,500%",
        "vencimiento": "09-jul-29",
        "tipo": "TASA_FIJA",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "676/2020"
    },
    
    # BONOS REP ARGENTINA USD - Soberanos en dólares
    "AR30D": {
        "nombre": "BONO REP. ARGENTINA USD STEP UP 2030",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 0,50% - 0,75% - 1,75%",
        "vencimiento": "09-jul-30",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AR35D": {
        "nombre": "BONO REP. ARGENTINA USD STEP UP 2035",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 1,125% - 1,50% - 3,625% - 4,125% - 4,75%- 5%",
        "vencimiento": "09-jul-35",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AR38D": {
        "nombre": "BONO REP. ARGENTINA USD STEP UP 2038",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 2% - 3,875% -  4,25%  - 5%",
        "vencimiento": "09-ene-38",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AR41D": {
        "nombre": "BONO REP. ARGENTINA USD STEP UP 2041",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "0,125% - 2,5% - 3,8% -  4,875%",
        "vencimiento": "09-jul-41",
        "tipo": "STEP_UP",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    "AR29D": {
        "nombre": "BONO REP. ARGENTINA USD 1% 2029",
        "fecha_emision": "04-sep-20",
        "tasa_interes": "1,000%",
        "vencimiento": "09-jul-29",
        "tipo": "TASA_FIJA",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "676/2020"
    },
    
    # BONOS PAR - Soberanos en pesos a tasa fija
    "PARP": {
        "nombre": "PAR PESOS (PAVP) - LEGISLACIÓN ARGENTINA",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "0,63% - 1,18 % - 1,77% - 2,48%",
        "vencimiento": "31-dic-38",
        "tipo": "PAR",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa fija",
        "decreto": "1735/2004"
    },
    "PARA": {
        "nombre": "PAR USD (PAVA) - LEGISLACIÓN ARGENTINA",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "1,33% - 2,5 % - 3,75% - 5,25%",
        "vencimiento": "31-dic-38",
        "tipo": "PAR",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "1735/2004"
    },
    "PARY": {
        "nombre": "PAR USD (PAVY) - LEGISLACIÓN N. YORK",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "1,33% - 2,5 % - 3,75% - 5,25%",
        "vencimiento": "31-dic-38",
        "tipo": "PAR",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "1735/2004"
    },
    "PARE": {
        "nombre": "PAR EUROS - LEGISLACIÓN LONDRES",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "1,20% - 2,26 % - 3,38% - 4,74%",
        "vencimiento": "31-dic-38",
        "tipo": "PAR",
        "moneda": "EUR",
        "categoria_scraping": "Soberanos en euros",
        "decreto": "1735/2004"
    },
    "PARYN": {
        "nombre": "PAR YENES - LEGISLACIÓN TOKIO",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "0,24% - 0,45 % - 0,67% - 0,94%",
        "vencimiento": "31-dic-38",
        "tipo": "PAR",
        "moneda": "JPY",
        "categoria_scraping": "Soberanos en yenes",
        "decreto": "1735/2004"
    },
    
    # BONOS DESCUENTO - Soberanos en pesos a tasa fija
    "DISCP": {
        "nombre": "DISC PESOS (DIVP) - LEGISLACIÓN ARGENTINA",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "5,83%",
        "vencimiento": "31-dic-33",
        "tipo": "DESCUENTO",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa fija",
        "decreto": "1735/2004"
    },
    "DISCA": {
        "nombre": "DISC USD (DIVA) - LEGISLACIÓN ARGENTINA",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "8,28%",
        "vencimiento": "31-dic-33",
        "tipo": "DESCUENTO",
        "moneda": "USD",
        "categoria_scraping": "Soberanos en dólares",
        "decreto": "1735/2004"
    },
    "DISCY": {
        "nombre": "DISC YENES - LEGISLACIÓN TOKIO",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "4,33%",
        "vencimiento": "31-dic-33",
        "tipo": "DESCUENTO",
        "moneda": "JPY",
        "categoria_scraping": "Soberanos en yenes",
        "decreto": "1735/2004"
    },
    "CUASIP": {
        "nombre": "CUASI-PAR PESOS - LEGISLACIÓN ARGENTINA",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "3,31%",
        "vencimiento": "31-dic-45",
        "tipo": "CUASIPAR",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa fija",
        "decreto": "1735/2004"
    },
    
    # UNIDADES VINCULADAS AL PBI - Cupones vinculados al PBI
    "PBI_PESOS": {
        "nombre": "Unidades Vinculadas al PBI en pesos bajo legislación Argentina",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "Variable según PBI",
        "vencimiento": "15-dic-35",
        "tipo": "PBI_LINKED",
        "moneda": "PESOS",
        "categoria_scraping": "Cupones vinculados al PBI",
        "decreto": "1735/2004"
    },
    "PBI_USD": {
        "nombre": "Unidades Vinculadas al PBI en USD bajo legislación Argentina",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "Variable según PBI",
        "vencimiento": "15-dic-35",
        "tipo": "PBI_LINKED",
        "moneda": "USD",
        "categoria_scraping": "Cupones vinculados al PBI",
        "decreto": "1735/2004"
    },
    "PBI_USD_NY": {
        "nombre": "Unidades Vinculadas al PBI en USD bajo legislación N. York",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "Variable según PBI",
        "vencimiento": "15-dic-35",
        "tipo": "PBI_LINKED",
        "moneda": "USD",
        "categoria_scraping": "Cupones vinculados al PBI",
        "decreto": "1735/2004"
    },
    "PBI_EUR": {
        "nombre": "Unidades Vinculadas al PBI en euros bajo legislación de Londres",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "Variable según PBI",
        "vencimiento": "15-dic-35",
        "tipo": "PBI_LINKED",
        "moneda": "EUR",
        "categoria_scraping": "Cupones vinculados al PBI",
        "decreto": "1735/2004"
    },
    "PBI_JPY": {
        "nombre": "Unidades Vinculadas al PBI en yenes bajo legislación de Tokio",
        "fecha_emision": "31-dic-03",
        "tasa_interes": "Variable según PBI",
        "vencimiento": "15-dic-35",
        "tipo": "PBI_LINKED",
        "moneda": "JPY",
        "categoria_scraping": "Cupones vinculados al PBI",
        "decreto": "1735/2004"
    },
    
    # BONARES - Soberanos en pesos a tasa fija
    "BONAR2028": {
        "nombre": "BONOS DE LA NACIÓN ARGENTINA PARA EL CONSENSO FISCAL",
        "fecha_emision": "03-abr-18",
        "tasa_interes": "6,73%",
        "vencimiento": "31-dic-28",
        "tipo": "BONAR",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa fija",
        "decreto": "Nacional"
    },
    
    # BONTES - Soberanos en pesos a tasa variable
    "BONTE2026": {
        "nombre": "BONOS DEL TESORO NACIONAL EN PESOS A TASA FIJA VENCIMIENTO 17 DE OCTUBRE DE 2026",
        "fecha_emision": "17-oct-16",
        "tasa_interes": "15,50%",
        "vencimiento": "17-oct-26",
        "tipo": "BONTE",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa fija",
        "decreto": "Nacional"
    },
    "BONTE2030": {
        "nombre": "BONTE EN PESOS A TASA BADLAR VTO JULIO 2030",
        "fecha_emision": "05-jul-21",
        "tasa_interes": "BADLAR",
        "vencimiento": "05-jul-30",
        "tipo": "BONTE",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa variable",
        "decreto": "Nacional"
    },
    "BONTE2031": {
        "nombre": "BONTE EN PESOS A TASA BADLAR VTO AGOSTO 2031",
        "fecha_emision": "17-ago-21",
        "tasa_interes": "BADLAR + 400 PB",
        "vencimiento": "17-ago-31",
        "tipo": "BONTE",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa variable",
        "decreto": "Nacional"
    },
    "BONTE2026DIC": {
        "nombre": "BONTE EN PESOS A TASA BADLAR VTO DICIEMBRE 2026",
        "fecha_emision": "22-dic-21",
        "tasa_interes": "BADLAR",
        "vencimiento": "22-dic-26",
        "tipo": "BONTE",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa variable",
        "decreto": "Nacional"
    },
    "BONTE2027": {
        "nombre": "BONTE EN PESOS VTO MAYO 2027",
        "fecha_emision": "23-may-22",
        "tasa_interes": "La menor entre 43,25% o 1%+CER",
        "vencimiento": "23-may-27",
        "tipo": "BONTE",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos en pesos a tasa variable",
        "decreto": "Nacional"
    },
    
    # BONCAP - Letras en pesos
    "BONCAP2025OCT": {
        "nombre": "BONO CAPITALIZABLE TASA CERO VTO OCTUBRE 2025",
        "fecha_emision": "14-oct-24",
        "tasa_interes": "3,90%",
        "vencimiento": "17-oct-25",
        "tipo": "BONCAP",
        "moneda": "PESOS",
        "categoria_scraping": "Letras en pesos",
        "decreto": "Nacional"
    },
    "BONCAP2025DIC": {
        "nombre": "BONO CAPITALIZABLE TASA CERO VTO DICIEMBRE 2025",
        "fecha_emision": "14-oct-24",
        "tasa_interes": "3,89%",
        "vencimiento": "15-dic-25",
        "tipo": "BONCAP",
        "moneda": "PESOS",
        "categoria_scraping": "Letras en pesos",
        "decreto": "Nacional"
    },
    "BONCAP2026FEB": {
        "nombre": "BONO CAPITALIZABLE TASA CERO VTO FEBRERO 2026",
        "fecha_emision": "29-nov-24",
        "tasa_interes": "2,60%",
        "vencimiento": "13-feb-26",
        "tipo": "BONCAP",
        "moneda": "PESOS",
        "categoria_scraping": "Letras en pesos",
        "decreto": "Nacional"
    },
    "BONCAP2026JUN": {
        "nombre": "BONO CAPITALIZABLE TASA CERO VTO JUNIO 2026",
        "fecha_emision": "17-ene-25",
        "tasa_interes": "2,15%",
        "vencimiento": "30-jun-26",
        "tipo": "BONCAP",
        "moneda": "PESOS",
        "categoria_scraping": "Letras en pesos",
        "decreto": "Nacional"
    },
    "BONCAP2026ENE": {
        "nombre": "BONO CAPITALIZABLE TASA CERO VTO FEBRERO 2026",
        "fecha_emision": "16-dic-24",
        "tasa_interes": "2,60%",
        "vencimiento": "30-dic-26",
        "tipo": "BONCAP",
        "moneda": "PESOS",
        "categoria_scraping": "Letras en pesos",
        "decreto": "Nacional"
    },
    "BONCAP2027ENE": {
        "nombre": "BONO CAPITALIZABLE TASA CERO VTO ENERO 2027",
        "fecha_emision": "31-ene-25",
        "tasa_interes": "2,05%",
        "vencimiento": "15-ene-27",
        "tipo": "BONCAP",
        "moneda": "PESOS",
        "categoria_scraping": "Letras en pesos",
        "decreto": "Nacional"
    },
    
    # BONAD DUAL - Soberanos dolar linked
    "BONAD2026MAR": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 16-03-2026",
        "fecha_emision": "31-ene-25",
        "tasa_interes": "CER+2,25% o tasa efectiva mensual TAMAR TEM",
        "vencimiento": "16-mar-26",
        "tipo": "BONAD_DUAL",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    "BONAD2026JUN": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 30-06-2026",
        "fecha_emision": "31-ene-25",
        "tasa_interes": "CER+2,19% o tasa efectiva mensual TAMAR TEM",
        "vencimiento": "30-jun-26",
        "tipo": "BONAD_DUAL",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    "BONAD2026SEP": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 15-09-2026",
        "fecha_emision": "31-ene-25",
        "tasa_interes": "CER+2,17% o tasa efectiva mensual TAMAR TEM",
        "vencimiento": "15-sep-26",
        "tipo": "BONAD_DUAL",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    "BONAD2026DIC": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 15-12-2026",
        "fecha_emision": "31-ene-25",
        "tasa_interes": "CER+2,14% o tasa efectiva mensual TAMAR TEM",
        "vencimiento": "15-dic-26",
        "tipo": "BONAD_DUAL",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    "BONAD2036SEP": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 29-09-2036",
        "fecha_emision": "20-oct-23",
        "tasa_interes": "CER+3% o rendimiento del tipo de cambio",
        "vencimiento": "29-sep-36",
        "tipo": "BONAD_DUAL",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    
    # BONTE DLK - Soberanos dolar linked
    "BONTE_DLK2025JUN": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 30-06-2025",
        "fecha_emision": "28-feb-24",
        "tasa_interes": "0,00%",
        "vencimiento": "30-jun-25",
        "tipo": "BONTE_DLK",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    "BONTE_DLK2025DIC": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 15-12-2025",
        "fecha_emision": "01-jul-24",
        "tasa_interes": "0,00%",
        "vencimiento": "15-dic-25",
        "tipo": "BONTE_DLK",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    "BONTE_DLK2026JUN": {
        "nombre": "BONO DEL TESORO NACIONAL VINCULADO AL DÓLAR 30-06-2026",
        "fecha_emision": "01-jul-24",
        "tasa_interes": "0,00%",
        "vencimiento": "30-jun-26",
        "tipo": "BONTE_DLK",
        "moneda": "PESOS",
        "categoria_scraping": "Soberanos dolar linked",
        "decreto": "Nacional"
    },
    
    # BOCON - Provinciales en pesos
    "BOCON_PROV": {
        "nombre": "BOCON PROVEEDORES 10ta. SERIE EN PESOS (PR 17)",
        "fecha_emision": "02-may-22",
        "tasa_interes": "BADLAR promedio bancos privados",
        "vencimiento": "02-may-29",
        "tipo": "BOCON",
        "moneda": "PESOS",
        "categoria_scraping": "Provinciales en pesos",
        "decreto": "Nacional"
    }
}

# Mapeo de categorías de scraping a tipos de bonos
CATEGORIAS_SCRAPING = {
    "Soberanos en pesos más Cer": ["BONCER"],
    "Soberanos en pesos a tasa variable": ["BONTE", "BONTE_DLK"],
    "Soberanos en pesos a tasa fija": ["BONAR", "BONTE", "PAR", "DESCUENTO", "CUASIPAR"],
    "Soberanos en dólares": ["STEP_UP", "PAR", "DESCUENTO"],
    "Soberanos dolar linked": ["BONAD_DUAL", "BONTE_DLK"],
    "Provinciales en pesos": ["BOCON"],
    "Provinciales dolar linked": [],
    "Provinciales en dólares": [],
    "Provinciales en euros": [],
    "Cupones vinculados al PBI": ["PBI_LINKED"],
    "Letras en pesos": ["BONCAP"],
    "Letras en dólares": []
}

# Función para obtener bonos por categoría de scraping
def obtener_bonos_por_categoria(categoria):
    """Obtiene todos los bonos de una categoría específica del scraping"""
    bonos_categoria = []
    for simbolo, info in INSTRUMENTOS_FINANCIEROS.items():
        if info.get('categoria_scraping') == categoria:
            bonos_categoria.append(simbolo)
    return bonos_categoria

# Función para obtener todas las categorías disponibles
def obtener_categorias_disponibles():
    """Obtiene todas las categorías de scraping disponibles"""
    categorias = set()
    for info in INSTRUMENTOS_FINANCIEROS.values():
        if 'categoria_scraping' in info:
            categorias.add(info['categoria_scraping'])
    return sorted(list(categorias))

def obtener_tabla(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    tablas = soup.find_all("table")
    if not tablas:
        return pd.DataFrame([{"Error": "No se encontró tabla en la página"}])
    tabla = tablas[0]
    df = pd.read_html(str(tabla))[0]
    return df

# --- Autenticación IOL ---
def obtener_tokens(usuario, contrasena):
    url_token = 'https://api.invertironline.com/token'
    datos = {
        'username': usuario,
        'password': contrasena,
        'grant_type': 'password'
    }
    encabezados = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    respuesta = requests.post(url_token, data=datos, headers=encabezados)
    if respuesta.status_code == 200:
        tokens = respuesta.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        st.write(f'Error en la solicitud de token: {respuesta.status_code}')
        return None, None

def refrescar_token(token_refresco):
    url_token = 'https://api.invertironline.com/token'
    datos = {
        'refresh_token': token_refresco,
        'grant_type': 'refresh_token'
    }
    encabezados = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    respuesta = requests.post(url_token, data=datos, headers=encabezados)
    if respuesta.status_code == 200:
        tokens = respuesta.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        st.write(f'Error al refrescar token: {respuesta.status_code}')
        return None, None

# --- Función para obtener serie histórica (endpoint correcto) ---
def obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return pd.DataFrame(data)
        else:
            st.write(f"No hay datos históricos para {simbolo}")
            return pd.DataFrame()
    else:
        st.write(f"Error al obtener serie histórica de {simbolo}: {response.status_code}")
        return pd.DataFrame()

def obtener_datos_tecnicos(url_detalle):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url_detalle, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        datos = {}
        
        # Método 1: Buscar elementos con atributos data-field específicos de IOL
        elementos_data = soup.find_all(attrs={"data-field": True})
        for elemento in elementos_data:
            campo = elemento.get("data-field")
            valor = elemento.get_text(strip=True)
            if campo and valor and valor != 'N/A' and valor != '-':
                datos[campo] = valor
        
        # Método 2: Buscar tablas específicas de datos técnicos
        tablas = soup.find_all("table", class_=["table", "table-striped", "table-condensed"])
        for tabla in tablas:
            try:
                filas = tabla.find_all("tr")
                for fila in filas:
                    celdas = fila.find_all(["td", "th"])
                    if len(celdas) >= 2:
                        # Buscar pares clave-valor en filas de tabla
                        for i in range(len(celdas) - 1):
                            clave = celdas[i].get_text(strip=True)
                            valor = celdas[i + 1].get_text(strip=True)
                            if clave and valor and valor != 'N/A' and valor != '-' and len(clave) < 100:
                                datos[clave] = valor
            except Exception as e:
                continue
        
        # Método 3: Buscar elementos con clases específicas de datos técnicos
        clases_tecnicas = [
            'technical-data', 'fundamental-data', 'bond-info', 'instrument-data',
            'data-field', 'technical-info', 'fundamental-info'
        ]
        for clase in clases_tecnicas:
            elementos = soup.find_all(class_=clase)
            for elemento in elementos:
                try:
                    # Buscar pares clave-valor en elementos hijos
                    hijos = elemento.find_all(["div", "span", "p", "li"])
                    for i in range(0, len(hijos) - 1, 2):
                        if i + 1 < len(hijos):
                            clave = hijos[i].get_text(strip=True)
                            valor = hijos[i + 1].get_text(strip=True)
                            if clave and valor and len(clave) < 100 and valor != 'N/A' and valor != '-':
                                datos[clave] = valor
                except Exception as e:
                    continue
        
        # Método 4: Buscar elementos con atributos específicos de IOL
        elementos_iol = soup.find_all(attrs={"data-quoteStyle": True})
        for elemento in elementos_iol:
            try:
                # Buscar elementos hermanos o padres que contengan datos
                padre = elemento.parent
                if padre:
                    texto_completo = padre.get_text(strip=True)
                    # Extraer valores numéricos y de moneda
                    import re
                    valores_moneda = re.findall(r'US\$[\s]*([\d,\.]+)', texto_completo)
                    valores_porcentaje = re.findall(r'([+-]?[\d,\.]+)\s*%', texto_completo)
                    
                    if valores_moneda:
                        datos['Precio_USD'] = valores_moneda[0]
                    if valores_porcentaje:
                        datos['Variacion_Porcentaje'] = valores_porcentaje[0]
            except Exception as e:
                continue
        
        # Método 5: Buscar elementos con IDs específicos de la página
        ids_especificos = ['IdTitulo', 'variacionUltimoPrecio', 'MontoOperado', 'VolumenNominal']
        for id_elem in ids_especificos:
            elemento = soup.find(id=id_elem)
            if elemento:
                valor = elemento.get_text(strip=True)
                if valor and valor != 'N/A' and valor != '-':
                    datos[id_elem] = valor
        
        # Método 6: Buscar elementos con clases específicas de la página de IOL
        clases_iol_especificas = [
            'fontsize18', 'down', 'up', 'list-unstyled',
            'header-tabla-cotizacion', 'table-striped'
        ]
        for clase in clases_iol_especificas:
            elementos = soup.find_all(class_=clase)
            for elemento in elementos:
                try:
                    # Buscar datos en elementos con estas clases
                    texto = elemento.get_text(strip=True)
                    if texto and len(texto) < 200:
                        # Extraer valores específicos
                        import re
                        # Buscar precios en USD
                        precios_usd = re.findall(r'US\$[\s]*([\d,\.]+)', texto)
                        if precios_usd:
                            datos['Precio_USD'] = precios_usd[0]
                        
                        # Buscar variaciones
                        variaciones = re.findall(r'([+-]?[\d,\.]+)\s*%', texto)
                        if variaciones:
                            datos['Variacion_Porcentaje'] = variaciones[0]
                        
                        # Buscar volúmenes
                        volumenes = re.findall(r'Q:\s*([\d,]+)', texto)
                        if volumenes:
                            datos['Volumen'] = volumenes[0]
                except Exception as e:
                    continue
        
        # Método 7: Buscar elementos con atributos data-field específicos
        elementos_data_field = soup.find_all(attrs={"data-field": True})
        for elemento in elementos_data_field:
            campo = elemento.get("data-field")
            valor = elemento.get_text(strip=True)
            if campo and valor and valor != 'N/A' and valor != '-':
                # Normalizar nombres de campos
                campo_normalizado = campo.replace(' ', '_').replace('-', '_')
                datos[campo_normalizado] = valor
        
        # Método 8: Buscar elementos con atributos data-quoteStyle
        elementos_quote_style = soup.find_all(attrs={"data-quoteStyle": True})
        for elemento in elementos_quote_style:
            try:
                # Buscar elementos hermanos que contengan datos
                hermanos = elemento.find_next_siblings()
                for hermano in hermanos:
                    texto = hermano.get_text(strip=True)
                    if texto and len(texto) < 100:
                        # Extraer valores específicos
                        import re
                        valores = re.findall(r'([\d,\.]+)', texto)
                        if valores:
                            datos['Valor_Quote'] = valores[0]
            except Exception as e:
                continue
        
        # Método 9: Buscar elementos con clases específicas de datos técnicos
        clases_datos_tecnicos = [
            'technical-indicators', 'fundamental-metrics', 'bond-metrics',
            'instrument-details', 'market-data'
        ]
        for clase in clases_datos_tecnicos:
            elementos = soup.find_all(class_=clase)
            for elemento in elementos:
                try:
                    # Buscar pares clave-valor en elementos hijos
                    hijos = elemento.find_all(["div", "span", "p", "li"])
                    for i in range(0, len(hijos) - 1, 2):
                        if i + 1 < len(hijos):
                            clave = hijos[i].get_text(strip=True)
                            valor = hijos[i + 1].get_text(strip=True)
                            if clave and valor and len(clave) < 100 and valor != 'N/A' and valor != '-':
                                datos[clave] = valor
                except Exception as e:
                    continue
        
        # Método 10: Buscar elementos con patrones específicos en el texto
        texto_completo = soup.get_text()
        patrones = [
            r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+):\s*([^\n\r]+)',
            r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)\s*=\s*([^\n\r]+)',
            r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)\s*:\s*([^\n\r]+)',
            r'Max:\s*US\$[\s]*([\d,\.]+)',
            r'Min:\s*US\$[\s]*([\d,\.]+)',
            r'Volumen Operado:\s*([^\n\r]+)',
            r'Rango del día:\s*([^\n\r]+)'
        ]
        
        for patron in patrones:
            matches = re.findall(patron, texto_completo)
            for match in matches:
                if len(match) == 2:
                    clave = match[0].strip()
                    valor = match[1].strip()
                    if len(clave) < 50 and len(valor) < 200 and valor != clave:
                        datos[clave] = valor
                elif len(match) == 1:
                    # Para patrones que solo extraen valores
                    valor = match[0].strip()
                    if valor and len(valor) < 200:
                        datos[f'Valor_{len(datos)}'] = valor
        
        # Limpiar y normalizar datos
        datos_limpios = {}
        for clave, valor in datos.items():
            clave_limpia = clave.strip()
            valor_limpio = valor.strip()
            
            # Filtrar claves muy largas o valores vacíos
            if (len(clave_limpia) < 100 and 
                len(valor_limpio) < 500 and 
                valor_limpio and 
                valor_limpio != 'N/A' and 
                valor_limpio != '-' and
                not clave_limpia.isdigit() and
                clave_limpia not in datos_limpios):  # Evitar duplicados
                datos_limpios[clave_limpia] = valor_limpio
        
        return datos_limpios
        
    except Exception as e:
        print(f"Error en obtener_datos_tecnicos: {str(e)}")
        return {}

def construir_url_fundamentales(simbolo, df_bonos):
    # Buscar el nombre real del bono en la tabla principal
    nombre_bono = None
    
    # Buscar en columnas que puedan contener el nombre del bono
    for col in df_bonos.columns:
        if any(palabra in col.lower() for palabra in ['especie', 'nombre', 'denominación', 'descripcion', 'descripción']):
            fila_bono = df_bonos[df_bonos.iloc[:, 0] == simbolo]  # Asumiendo que la primera columna es el símbolo
            if not fila_bono.empty:
                nombre_bono = str(fila_bono.iloc[0][col])
                break
    
    # Si no se encuentra, usar un nombre genérico
    if not nombre_bono or nombre_bono == 'nan':
        nombre_bono = "BONO-REP.-ARGENTINA-USD-STEP-UP-2038"
    
    # Formatear el nombre para la URL
    nombre_url = nombre_bono.upper().replace(" ", "-")
    nombre_url = ''.join((c for c in unicodedata.normalize('NFD', nombre_url) if unicodedata.category(c) != 'Mn'))
    nombre_url = nombre_url.replace('.', '').replace(',', '').replace('(', '').replace(')', '').replace('/', '').replace('--', '-')
    
    return f"https://iol.invertironline.com/titulo/cotizacion/BCBA/{simbolo}/{nombre_url}/fundamentalesTecnicos"

# --- BCRA: obtener CER ---
@st.cache_data(ttl=3600)
def get_bcra_cer(fecha_desde, fecha_hasta):
    url = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables_datos.asp"
    params = {
        'serie': '7935',  # CER diario
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'primeravez': '1'
    }
    try:
        response = requests.get(url, params=params, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'table'})
        if table and hasattr(table, 'find_all'):
            data = []
            try:
                if isinstance(table, bs4.element.Tag):
                    rows = table.find_all('tr')
                    if rows:
                        headers = []
                        try:
                            headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
                        except Exception as e:
                            print(f"Debug: Error procesando headers: {str(e)}")
                            headers = []
                        
                        for row in rows[1:]:
                            try:
                                cols = row.find_all('td')
                                if cols:
                                    row_data = [col.get_text(strip=True) for col in cols]
                                    data.append(row_data)
                            except Exception as e:
                                print(f"Debug: Error procesando fila BCRA: {str(e)}")
                                continue
            except Exception as e:
                print(f"Debug: Error procesando tabla BCRA: {str(e)}")
            if data:
                df = pd.DataFrame(data, columns=headers)
                if 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
                    df = df.sort_values('Fecha')
                if 'Valor' in df.columns:
                    df['Valor'] = pd.to_numeric(df['Valor'].str.replace(',', '.'), errors='coerce')
                df = df.set_index('Fecha')
                return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error al obtener CER: {str(e)}")
        return pd.DataFrame()

# --- Variables globales ---
# Inicialización de variables de sesión (comentado para evitar errores del linter)
# if 'series_historicas' not in st.session_state:
#     st.session_state['series_historicas'] = {}
# if 'datos_tecnicos' not in st.session_state:
#     st.session_state['datos_tecnicos'] = {'Bonos': {}}
# if 'flujos_bonos' not in st.session_state:
#     st.session_state['flujos_bonos'] = {}
# if 'duration_bonos' not in st.session_state:
#     st.session_state['duration_bonos'] = {}
# if 'clasificacion_bonos' not in st.session_state:
#     st.session_state['clasificacion_bonos'] = {}

# --- Lógica inteligente para flujo y clasificación ---
def clasificar_bono(datos_tecnicos, panel):
    # Clasificación básica por panel y texto
    forma = datos_tecnicos.get('Forma de amortización', '').lower()
    denom = datos_tecnicos.get('Denominación', '').lower()
    if 'cer' in forma or 'cer' in denom:
        return 'Soberano en pesos más CER'
    if 'dólar linked' in forma or 'dólar linked' in denom or 'dolar linked' in forma or 'dolar linked' in denom:
        return 'Soberano dólar linked'
    if 'provincial' in denom or 'provincia' in denom:
        return 'Provincial'
    if 'euros' in denom or 'euros' in forma:
        return 'Soberano en euros'
    if 'pesos' in denom or 'pesos' in forma:
        if 'variable' in forma:
            return 'Soberano en pesos a tasa variable'
        if 'fija' in forma:
            return 'Soberano en pesos a tasa fija'
        return 'Soberano en pesos'
    if 'dólares' in denom or 'dólares' in forma or 'dolares' in denom or 'dolares' in forma:
        return 'Soberano en dólares'
    return panel

def armar_flujo_y_duration(datos_tecnicos, simbolo):
    try:
        fecha_emision = datos_tecnicos.get('Fecha de Emisión')
        fecha_venc = datos_tecnicos.get('Fecha Vencimiento')
        monto_nominal = datos_tecnicos.get('Monto nominal vigente en la moneda original de emisión')
        interes = datos_tecnicos.get('Interés')
        forma_amort = datos_tecnicos.get('Forma de amortización')
        denominacion_min = datos_tecnicos.get('Denominación mínima')
        moneda = datos_tecnicos.get('Moneda de emisión')
        if not (fecha_emision and fecha_venc and interes and forma_amort):
            return None, None, 'Faltan datos técnicos clave.'
        # Parsear fechas
        fecha_emision_dt = parse(fecha_emision, dayfirst=True)
        fecha_venc_dt = parse(fecha_venc, dayfirst=True)
        # Detectar pagos semestrales
        pagos_semestrales = 'semestral' in forma_amort.lower() or '6 meses' in forma_amort.lower()
        # Detectar cuotas
        cuotas_match = re.search(r'(\d+) cuotas', forma_amort)
        n_cuotas = int(cuotas_match.group(1)) if cuotas_match else None
        # Detectar fechas de pago explícitas
        fechas_pago = []
        if pagos_semestrales and n_cuotas:
            # Buscar primer pago en la descripción
            primer_pago_match = re.search(r'comenzando el (\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})', forma_amort)
            if primer_pago_match:
                primer_pago = parse(primer_pago_match.group(1), dayfirst=True)
            else:
                primer_pago = fecha_emision_dt + pd.DateOffset(months=6)
            fechas_pago = [primer_pago + pd.DateOffset(months=6*i) for i in range(n_cuotas)]
        elif n_cuotas:
            fechas_pago = [fecha_emision_dt + pd.DateOffset(months=12*i) for i in range(n_cuotas)]
        else:
            # Bullet: todo al final
            fechas_pago = [fecha_venc_dt]
            n_cuotas = 1
        # Parsear tasas
        tasas = re.findall(r'(\d+[\.,]?\d*)\s*%', interes)
        tasas = [float(t.replace(',', '.'))/100 for t in tasas]
        tasa = tasas[-1] if tasas else 0.0
        # Parsear nominal
        try:
            nominal = float(monto_nominal.replace('.', '').replace(',', '.')) if monto_nominal and monto_nominal != '-' else 100.0
        except:
            nominal = 100.0
        # Detectar si requiere CER
        requiere_cer = 'cer' in forma_amort.lower() or 'cer' in interes.lower() or 'cer' in datos_tecnicos.get('Denominación', '').lower()
        if requiere_cer:
            # Obtener CER para cada fecha
            cer_df = get_bcra_cer(fechas_pago[0].strftime('%Y-%m-%d'), fechas_pago[-1].strftime('%Y-%m-%d'))
            if cer_df.empty:
                return None, None, 'No se pudo obtener la serie CER del BCRA.'
            cer_emision = cer_df.iloc[0]['Valor']
            flujos = []
            for fecha in fechas_pago:
                if fecha in cer_df.index:
                    coef = cer_df.loc[fecha]['Valor'] / cer_emision
                else:
                    coef = 1
                # Ajustar capital e intereses (simplificado: cuota igual + interés)
                cuota_capital = nominal / n_cuotas
                cupon = cuota_capital * tasa  # Aproximación, puede requerir ajuste según bono
                flujo = (cuota_capital + cupon) * coef
                flujos.append(flujo)
            flujo_df = pd.DataFrame({'fecha': fechas_pago, 'flujo': flujos, 'coef_CER': [cer_df.loc[fecha]['Valor']/cer_emision if fecha in cer_df.index else None for fecha in fechas_pago]})
        else:
            # Estructura estándar
            cupon = nominal * tasa / (2 if pagos_semestrales else 1)
            if n_cuotas > 1:
                flujos = [cupon] * (n_cuotas - 1) + [cupon + nominal]
            else:
                flujos = [nominal + cupon]
            flujo_df = pd.DataFrame({'fecha': fechas_pago, 'flujo': flujos})
        # Calcular duration de Macaulay
        hoy = pd.Timestamp.today()
        flujos_desc = []
        t = []
        for i, row in flujo_df.iterrows():
            ti = (row['fecha'] - hoy).days / 365.25
            if ti < 0:
                ti = 0
            t.append(ti)
            flujos_desc.append(row['flujo'] / (1 + tasa/(2 if pagos_semestrales else 1)) ** (i+1))
        pv_total = sum(flujos_desc)
        if pv_total == 0:
            return flujo_df, None, 'El valor presente es cero.'
        duration = sum([ti * fd for ti, fd in zip(t, flujos_desc)]) / pv_total
        return flujo_df, duration, None
    except Exception as e:
        return None, None, f'Error: {e}'

def verificar_y_corregir_url_fundamentales(simbolo, url_original):
    """
    Verifica si la URL de fundamentales técnicos es accesible y la corrige si es necesario
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        # Intentar acceder a la URL original
        resp = requests.get(url_original, headers=headers, allow_redirects=True)
        
        # Si la respuesta es exitosa, usar la URL final (después de redirecciones)
        if resp.status_code == 200:
            url_final = resp.url
            print(f"Debug: {simbolo} - URL final después de redirección: {url_final}")
            return url_final
        else:
            print(f"Debug: {simbolo} - Error {resp.status_code} en URL: {url_original}")
            
            # Intentar con formato alternativo
            url_alternativa = f"https://iol.invertironline.com/titulo/cotizacion/BCBA/{simbolo}/BONO-REP.-ARGENTINA-USD-STEP-UP-2038/fundamentalesTecnicos"
            resp_alt = requests.get(url_alternativa, headers=headers, allow_redirects=True)
            
            if resp_alt.status_code == 200:
                print(f"Debug: {simbolo} - URL alternativa funciona: {resp_alt.url}")
                return resp_alt.url
            else:
                print(f"Debug: {simbolo} - URL alternativa también falla: {resp_alt.status_code}")
                return url_original  # Devolver la original como fallback
                
    except Exception as e:
        print(f"Debug: {simbolo} - Error verificando URL: {str(e)}")
        return url_original

def obtener_links_bonos(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    tabla = soup.find("table")
    simbolo_a_href = {}
    if tabla and hasattr(tabla, 'find_all'):
        try:
            if isinstance(tabla, bs4.element.Tag):
                for row in tabla.find_all("tr"):
                    try:
                        a_tag = row.find("a", attrs={"data-symbol": True, "href": True})
                        if a_tag:
                            simbolo = a_tag["data-symbol"]
                            href = a_tag["href"]
                            if isinstance(href, list):
                                href = href[0]
                            
                            # Extraer el nombre del bono del título
                            nombre_bono = ""
                            span_tooltip = a_tag.find("span", attrs={"data-toggle": "tooltip"})
                            if span_tooltip and span_tooltip.get("data-original-title"):
                                nombre_bono = span_tooltip.get("data-original-title")
                            elif span_tooltip and span_tooltip.get("title"):
                                nombre_bono = span_tooltip.get("title")
                            
                            # Si no se encontró el nombre, usar el símbolo
                            if not nombre_bono:
                                nombre_bono = simbolo
                            
                            # Formatear el nombre del bono para la URL
                            nombre_url = nombre_bono.upper().replace(" ", "-").replace(",", "").replace("(", "").replace(")", "").replace("/", "").replace("--", "-")
                            # Mantener los puntos como en la URL real de IOL
                            nombre_url = ''.join((c for c in unicodedata.normalize('NFD', nombre_url) if unicodedata.category(c) != 'Mn'))
                            
                            # Construir URL con el formato correcto: BCBA/MERCADO/TICKER/NOMBRE_BONO/fundamentalesTecnicos
                            url_fundamentales = f"https://iol.invertironline.com/titulo/cotizacion/BCBA/{simbolo}/{nombre_url}/fundamentalesTecnicos"
                            
                            # Debug: mostrar la URL construida
                            print(f"Debug: {simbolo} -> {url_fundamentales}")
                            print(f"Debug: Nombre del bono: {nombre_bono}")
                            print(f"Debug: Nombre formateado: {nombre_url}")
                            
                            simbolo_a_href[simbolo] = url_fundamentales
                    except Exception as e:
                        print(f"Debug: Error procesando fila en obtener_links_bonos: {str(e)}")
                        continue
        except Exception as e:
            print(f"Debug: Error procesando tabla en obtener_links_bonos: {str(e)}")
    return simbolo_a_href

def obtener_datos_basicos_bono(url_detalle):
    """Extrae datos básicos del bono desde la página principal (sin necesidad de autenticación)"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url_detalle, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        datos = {}
        
        # Buscar el título del bono
        titulo_h1 = soup.find("h1", class_="header-title")
        if titulo_h1:
            datos["Nombre del Bono"] = titulo_h1.get_text(strip=True)
        
        # Usar la función específica para extraer datos técnicos
        datos_tecnicos = extraer_datos_tecnicos_especificos(url_detalle)
        datos.update(datos_tecnicos)
        
        # Buscar datos en la tabla de cotización como respaldo
        tabla_cotizacion = soup.find("table", class_="table table-striped table-condensed")
        if tabla_cotizacion and hasattr(tabla_cotizacion, 'find_all'):
            try:
                if isinstance(tabla_cotizacion, bs4.element.Tag):
                    filas = tabla_cotizacion.find_all("tr")
                    for fila in filas:
                        try:
                            celdas = fila.find_all("td")
                            if len(celdas) >= 2:
                                # Buscar etiquetas en las celdas
                                etiquetas = fila.find_all("th")
                                if etiquetas:
                                    for i, etiqueta in enumerate(etiquetas):
                                        if i < len(celdas):
                                            clave = etiqueta.get_text(strip=True)
                                            valor = celdas[i].get_text(strip=True)
                                            if clave and valor and clave not in datos:
                                                datos[clave] = valor
                        except Exception as e:
                            print(f"Debug: Error procesando fila en datos básicos: {str(e)}")
                            continue
            except Exception as e:
                print(f"Debug: Error procesando tabla de cotización: {str(e)}")
        
        # Buscar información adicional en spans con data-field como respaldo
        spans_data = soup.find_all("span", attrs={"data-field": True})
        for span in spans_data:
            campo = span.get("data-field")
            valor = span.get_text(strip=True)
            if campo and valor and campo not in datos:
                datos[campo] = valor
        
        return datos
    except Exception as e:
        print(f"Debug: Error en obtener_datos_basicos_bono: {str(e)}")
        return {}

def verificar_autenticacion_requerida(url_detalle):
    """Verifica si la página requiere autenticación"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url_detalle, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Buscar indicadores de que se requiere login
        login_indicators = [
            "Ingresar",
            "Registrarse", 
            "Login",
            "Términos y Condiciones",
            "Aceptar"
        ]
        
        texto_pagina = soup.get_text().lower()
        for indicator in login_indicators:
            if indicator.lower() in texto_pagina:
                return True
        
        # Verificar si hay formularios de login
        forms = soup.find_all("form")
        for form in forms:
            if "login" in str(form).lower() or "password" in str(form).lower():
                return True
        
        return False
    except Exception as e:
        print(f"Debug: Error verificando autenticación: {str(e)}")
        return True  # Por defecto asumir que requiere autenticación

# --- Variables globales para el scraping automático ---
paneles_disponibles = list(urls.keys())

def mostrar_urls_fundamentales(panel_nombre):
    """
    Muestra las URLs de fundamentales técnicos que se construirán para un panel
    """
    if panel_nombre not in urls:
        return {}
    
    url_panel = urls[panel_nombre]
    simbolo_a_href = obtener_links_bonos(url_panel)
    
    if not simbolo_a_href:
        st.write(f"No se encontraron links para símbolos en {panel_nombre}")
        return {}
    
    st.write(f"### URLs de fundamentales técnicos para {panel_nombre}:")
    st.write(f"Total de símbolos encontrados: {len(simbolo_a_href)}")
    
    # Mostrar las primeras 10 URLs como ejemplo
    ejemplos = list(simbolo_a_href.items())[:10]
    for simbolo, url in ejemplos:
        st.write(f"- **{simbolo}**: {url}")
    
    if len(simbolo_a_href) > 10:
        st.write(f"... y {len(simbolo_a_href) - 10} símbolos más")
    
    return simbolo_a_href

def scraping_automatico_panel(panel_nombre, max_simbolos=None):
    """
    Realiza scraping automático de datos técnicos para todos los símbolos de un panel
    """
    if panel_nombre not in urls:
        return {}
    
    url_panel = urls[panel_nombre]
    print(f"Iniciando scraping automático para panel: {panel_nombre}")
    
    # Obtener tabla principal del panel
    df_panel = obtener_tabla(url_panel)
    if df_panel.empty or "Error" in df_panel.columns:
        print(f"No se pudo obtener la tabla del panel {panel_nombre}")
        return {}
    
    # Obtener links de todos los símbolos
    simbolo_a_href = obtener_links_bonos(url_panel)
    if not simbolo_a_href:
        print(f"No se encontraron links para símbolos en {panel_nombre}")
        return {}
    
    # Limitar número de símbolos si se especifica
    if max_simbolos:
        simbolo_a_href = dict(list(simbolo_a_href.items())[:max_simbolos])
    
    datos_completos = {}
    total_simbolos = len(simbolo_a_href)
    
    print(f"Procesando {total_simbolos} símbolos...")
    
    for i, (simbolo, href) in enumerate(simbolo_a_href.items(), 1):
        try:
            print(f"Procesando símbolo {i}/{total_simbolos}: {simbolo}")
            print(f"URL a procesar: {href}")
            
            # Obtener datos técnicos
            datos_tecnicos = obtener_datos_tecnicos(href)
            
            if datos_tecnicos:
                datos_completos[simbolo] = datos_tecnicos
                print(f"✓ Datos obtenidos para {simbolo}: {len(datos_tecnicos)} campos")
            else:
                print(f"✗ No se obtuvieron datos para {simbolo}")
            
            # Pausa pequeña para no sobrecargar el servidor
            import time
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error procesando {simbolo}: {str(e)}")
            continue
    
    print(f"Scraping completado. Datos obtenidos para {len(datos_completos)} símbolos")
    return datos_completos

def mostrar_resultados_scraping(datos_completos, panel_nombre):
    """
    Muestra los resultados del scraping de forma organizada
    """
    if not datos_completos:
        st.write(f"No se obtuvieron datos para el panel {panel_nombre}")
        return
    
    st.write(f"## Datos técnicos obtenidos para {panel_nombre}")
    st.write(f"Total de símbolos procesados: {len(datos_completos)}")
    
    # Crear DataFrame con todos los datos
    filas = []
    for simbolo, datos in datos_completos.items():
        fila = {'Símbolo': simbolo}
        fila.update(datos)
        filas.append(fila)
    
    if filas:
        df_resultados = pd.DataFrame(filas)
        st.write("### Resumen de datos obtenidos:")
        st.dataframe(df_resultados, use_container_width=True)
        
        # Mostrar estadísticas
        st.write("### Estadísticas:")
        st.write(f"- Símbolos con datos: {len(datos_completos)}")
        st.write(f"- Campos promedio por símbolo: {df_resultados.shape[1] - 1}")
        
        # Mostrar campos más comunes
        campos_comunes = []
        for datos in datos_completos.values():
            campos_comunes.extend(datos.keys())
        
        from collections import Counter
        campos_frecuentes = Counter(campos_comunes).most_common(10)
        
        st.write("### Campos más frecuentes:")
        for campo, frecuencia in campos_frecuentes:
            st.write(f"- {campo}: {frecuencia} símbolos")
    else:
        st.write("No se encontraron datos estructurados")

# --- Funciones de extracción de datos técnicos ---

def extraer_datos_tecnicos_especificos(url_detalle):
    """
    Función específica para extraer los datos técnicos más importantes del bono
    basándose en la estructura HTML de IOL
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url_detalle, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        datos_tecnicos = {}
        
        # 1. Extraer último precio operado
        elemento_precio = soup.find("span", {"data-field": "UltimoPrecio"})
        if elemento_precio:
            precio_texto = elemento_precio.get_text(strip=True)
            if precio_texto:
                datos_tecnicos['UltimoPrecio'] = precio_texto
        
        # 2. Extraer variación diaria
        elemento_variacion = soup.find("span", {"data-field": "Variacion"})
        if elemento_variacion:
            variacion_texto = elemento_variacion.get_text(strip=True)
            if variacion_texto:
                datos_tecnicos['Variacion'] = variacion_texto
        
        # 3. Extraer variación en puntos
        elemento_variacion_puntos = soup.find("span", {"data-field": "VariacionPuntos"})
        if elemento_variacion_puntos:
            variacion_puntos = elemento_variacion_puntos.get_text(strip=True)
            if variacion_puntos:
                datos_tecnicos['VariacionPuntos'] = variacion_puntos
        
        # 4. Extraer monto operado
        elemento_monto = soup.find("li", {"data-field": "MontoOperado"})
        if elemento_monto:
            monto_texto = elemento_monto.get_text(strip=True)
            if monto_texto:
                datos_tecnicos['MontoOperado'] = monto_texto
        
        # 5. Extraer volumen nominal
        elemento_volumen = soup.find("li", {"data-field": "VolumenNominal"})
        if elemento_volumen:
            volumen_texto = elemento_volumen.get_text(strip=True)
            if volumen_texto:
                datos_tecnicos['VolumenNominal'] = volumen_texto
        
        # 6. Extraer máximo del día
        elemento_maximo = soup.find("li", {"data-field": "Maximo"})
        if elemento_maximo:
            maximo_texto = elemento_maximo.get_text(strip=True)
            if maximo_texto:
                datos_tecnicos['Maximo'] = maximo_texto
        
        # 7. Extraer mínimo del día
        elemento_minimo = soup.find("li", {"data-field": "Minimo"})
        if elemento_minimo:
            minimo_texto = elemento_minimo.get_text(strip=True)
            if minimo_texto:
                datos_tecnicos['Minimo'] = minimo_texto
        
        # 8. Buscar datos en la tabla principal de cotización
        tabla_cotizacion = soup.find("table", {"class": "table-striped"})
        if tabla_cotizacion and hasattr(tabla_cotizacion, 'find_all'):
            try:
                if isinstance(tabla_cotizacion, bs4.element.Tag):
                    filas = tabla_cotizacion.find_all("tr")
                    for fila in filas:
                        celdas = fila.find_all(["td", "th"])
                        if len(celdas) >= 2:
                            # Buscar datos específicos en las celdas
                            for i, celda in enumerate(celdas):
                                texto_celda = celda.get_text(strip=True)
                                
                                # Buscar precios en USD
                                if 'US$' in texto_celda:
                                    import re
                                    precios = re.findall(r'US\$[\s]*([\d,\.]+)', texto_celda)
                                    if precios:
                                        datos_tecnicos['Precio_USD'] = precios[0]
                                
                                # Buscar variaciones porcentuales
                                if '%' in texto_celda:
                                    import re
                                    variaciones = re.findall(r'([+-]?[\d,\.]+)\s*%', texto_celda)
                                    if variaciones:
                                        datos_tecnicos['Variacion_Porcentaje'] = variaciones[0]
                                
                                # Buscar volúmenes
                                if 'Q:' in texto_celda:
                                    import re
                                    volumenes = re.findall(r'Q:\s*([\d,]+)', texto_celda)
                                    if volumenes:
                                        datos_tecnicos['Volumen'] = volumenes[0]
            except Exception as e:
                print(f"Debug: Error procesando tabla de cotización: {str(e)}")
        
        # 9. Buscar datos en elementos con clases específicas
        elementos_fontsize18 = soup.find_all("span", class_="fontsize18")
        for elemento in elementos_fontsize18:
            texto = elemento.get_text(strip=True)
            if texto:
                # Extraer precios USD
                import re
                precios_usd = re.findall(r'US\$[\s]*([\d,\.]+)', texto)
                if precios_usd and 'Precio_USD' not in datos_tecnicos:
                    datos_tecnicos['Precio_USD'] = precios_usd[0]
                
                # Extraer variaciones
                variaciones = re.findall(r'([+-]?[\d,\.]+)\s*%', texto)
                if variaciones and 'Variacion_Porcentaje' not in datos_tecnicos:
                    datos_tecnicos['Variacion_Porcentaje'] = variaciones[0]
        
        # 10. Buscar datos en elementos con clases up/down
        elementos_variacion = soup.find_all("span", class_=["up", "down"])
        for elemento in elementos_variacion:
            texto = elemento.get_text(strip=True)
            if texto:
                import re
                # Extraer variaciones en puntos
                variaciones_puntos = re.findall(r'US\$[\s]*([+-]?[\d,\.]+)', texto)
                if variaciones_puntos and 'VariacionPuntos' not in datos_tecnicos:
                    datos_tecnicos['VariacionPuntos'] = variaciones_puntos[0]
                
                # Extraer porcentajes
                porcentajes = re.findall(r'([+-]?[\d,\.]+)\s*%', texto)
                if porcentajes and 'Variacion_Porcentaje' not in datos_tecnicos:
                    datos_tecnicos['Variacion_Porcentaje'] = porcentajes[0]
        
        # 11. Buscar datos en listas no estructuradas
        listas_unstyled = soup.find_all("ul", class_="list-unstyled")
        for lista in listas_unstyled:
            elementos_li = lista.find_all("li")
            for elemento_li in elementos_li:
                texto = elemento_li.get_text(strip=True)
                if texto:
                    # Extraer montos operados
                    if 'US$' in texto and 'MontoOperado' not in datos_tecnicos:
                        datos_tecnicos['MontoOperado'] = texto
                    
                    # Extraer volúmenes
                    if 'Q:' in texto and 'VolumenNominal' not in datos_tecnicos:
                        datos_tecnicos['VolumenNominal'] = texto
                    
                    # Extraer máximos y mínimos
                    if 'Max:' in texto and 'Maximo' not in datos_tecnicos:
                        datos_tecnicos['Maximo'] = texto
                    elif 'Min:' in texto and 'Minimo' not in datos_tecnicos:
                        datos_tecnicos['Minimo'] = texto
        
        # 12. Buscar datos en elementos con atributos data-quoteStyle
        elementos_quote_style = soup.find_all(attrs={"data-quoteStyle": True})
        for elemento in elementos_quote_style:
            texto = elemento.get_text(strip=True)
            if texto:
                import re
                # Extraer valores numéricos
                valores = re.findall(r'([\d,\.]+)', texto)
                if valores:
                    datos_tecnicos['Valor_Quote'] = valores[0]
        
        # Limpiar y normalizar datos
        datos_limpios = {}
        for clave, valor in datos_tecnicos.items():
            if valor and valor != 'N/A' and valor != '-':
                datos_limpios[clave] = valor.strip()
        
        return datos_limpios
        
    except Exception as e:
        print(f"Error en extraer_datos_tecnicos_especificos: {str(e)}")
        return {}

def extraer_datos_tecnicos_bono(url_detalle):
    """
    Función específica para extraer los datos técnicos del bono
    desde la página de fundamentales técnicos
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url_detalle, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        datos_tecnicos = {}
        
        # Método 1: Buscar en el contenido completo por patrones específicos de datos técnicos
        texto_completo = soup.get_text()
        
        # Patrones específicos para datos técnicos de bonos
        patrones_tecnicos = [
            r'Emisor\s*([^\n\r]+)',
            r'Denominación\s*([^\n\r]+)',
            r'Tipo de Especie\s*([^\n\r]+)',
            r'Tipo de obligación\s*([^\n\r]+)',
            r'Moneda de emisión\s*([^\n\r]+)',
            r'Fecha de Emisión\s*([^\n\r]+)',
            r'Fecha Vencimiento\s*([^\n\r]+)',
            r'Monto nominal vigente en la moneda original de emisión\s*([^\n\r]+)',
            r'Monto residual en la moneda original de emisión\s*([^\n\r]+)',
            r'Interés\s*([^\n\r]+)',
            r'Forma de amortización\s*([^\n\r]+)',
            r'Denominación mínima\s*([^\n\r]+)',
            r'Tipo de garantía\s*([^\n\r]+)',
            r'Ley\s*([^\n\r]+)'
        ]
        
        for patron in patrones_tecnicos:
            matches = re.findall(patron, texto_completo, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if match and match.strip():
                    # Extraer el nombre del campo del patrón
                    nombre_campo = patron.split(r'\s*')[0]
                    datos_tecnicos[nombre_campo] = match.strip()
        
        # Método 2: Buscar en el div con id="datosTab" que se carga dinámicamente
        div_datos_tab = soup.find("div", {"id": "datosTab"})
        if div_datos_tab:
            # Buscar tablas dentro del div
            tablas = div_datos_tab.find_all("table")
            for tabla in tablas:
                try:
                    filas = tabla.find_all("tr")
                    for fila in filas:
                        celdas = fila.find_all(["td", "th"])
                        if len(celdas) >= 2:
                            etiqueta = celdas[0].get_text(strip=True)
                            valor = celdas[1].get_text(strip=True)
                            if etiqueta and valor and etiqueta != "Datos técnicos del bono":
                                datos_tecnicos[etiqueta.strip()] = valor.strip()
                except Exception as e:
                    continue
        
        # Método 3: Buscar en elementos con clases específicas de datos técnicos
        elementos_tecnicos = soup.find_all(["div", "span", "p"], class_=["technical-data", "fundamental-data", "bond-info"])
        for elemento in elementos_tecnicos:
            texto = elemento.get_text(strip=True)
            if texto and len(texto) < 500:
                # Buscar patrones de clave-valor
                import re
                patrones = [
                    r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+):\s*([^\n\r]+)',
                    r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)\s*=\s*([^\n\r]+)',
                    r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)\s*:\s*([^\n\r]+)'
                ]
                for patron in patrones:
                    matches = re.findall(patron, texto)
                    for match in matches:
                        if len(match) == 2:
                            clave = match[0].strip()
                            valor = match[1].strip()
                            if len(clave) < 100 and len(valor) < 200 and clave != valor:
                                datos_tecnicos[clave] = valor
        
        # Método 4: Buscar en listas de definición (dl/dt/dd)
        listas_definicion = soup.find_all("dl")
        for dl in listas_definicion:
            try:
                dts = dl.find_all("dt")
                dds = dl.find_all("dd")
                for i in range(min(len(dts), len(dds))):
                    clave = dts[i].get_text(strip=True)
                    valor = dds[i].get_text(strip=True)
                    if clave and valor and clave not in datos_tecnicos:
                        datos_tecnicos[clave] = valor
            except Exception as e:
                continue
        
        # Método 5: Buscar en elementos con atributos data-field específicos
        elementos_data_field = soup.find_all(attrs={"data-field": True})
        for elemento in elementos_data_field:
            campo = elemento.get("data-field")
            valor = elemento.get_text(strip=True)
            if campo and valor and valor != 'N/A' and valor != '-':
                # Normalizar nombres de campos
                campo_normalizado = campo.replace(' ', '_').replace('-', '_')
                datos_tecnicos[campo_normalizado] = valor
        
        # Método 6: Buscar en elementos con clases específicas de IOL
        clases_iol = ["bond-details", "instrument-info", "technical-indicators", "fundamental-metrics"]
        for clase in clases_iol:
            elementos = soup.find_all(class_=clase)
            for elemento in elementos:
                try:
                    # Buscar pares clave-valor en elementos hijos
                    hijos = elemento.find_all(["div", "span", "p", "li"])
                    for i in range(0, len(hijos) - 1, 2):
                        if i + 1 < len(hijos):
                            clave = hijos[i].get_text(strip=True)
                            valor = hijos[i + 1].get_text(strip=True)
                            if clave and valor and len(clave) < 100 and valor != 'N/A' and valor != '-':
                                datos_tecnicos[clave] = valor
                except Exception as e:
                    continue
        
        # Método 7: Buscar específicamente después del texto "Datos técnicos del bono"
        import re
        patron_datos_tecnicos = r'Datos técnicos del bono\s*(.*?)(?=\n\n|\Z)'
        match_datos_tecnicos = re.search(patron_datos_tecnicos, texto_completo, re.DOTALL | re.IGNORECASE)
        if match_datos_tecnicos:
            seccion_tecnicos = match_datos_tecnicos.group(1)
            # Buscar pares clave-valor en esta sección
            patrones_clave_valor = [
                r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)\s*([^\n\r]+)',
                r'([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+):\s*([^\n\r]+)'
            ]
            for patron in patrones_clave_valor:
                matches = re.findall(patron, seccion_tecnicos)
                for match in matches:
                    if len(match) == 2:
                        clave = match[0].strip()
                        valor = match[1].strip()
                        if clave and valor and len(clave) < 100 and valor != 'N/A' and valor != '-':
                            datos_tecnicos[clave] = valor
        
        # Limpiar y normalizar datos
        datos_limpios = {}
        for clave, valor in datos_tecnicos.items():
            if valor and valor != 'N/A' and valor != '-' and len(clave) < 100:
                datos_limpios[clave.strip()] = valor.strip()
        
        return datos_limpios
        
    except Exception as e:
        print(f"Error en extraer_datos_tecnicos_bono: {str(e)}")
        return {}

def probar_extraccion_datos_tecnicos(simbolo="AE38D"):
    """
    Función de prueba para verificar la extracción de datos técnicos
    """
    # Construir URL de prueba
    url_prueba = f"https://iol.invertironline.com/titulo/cotizacion/BCBA/{simbolo}/BONO-REP.-ARGENTINA-USD-STEP-UP-2038/fundamentalesTecnicos"
    
    print(f"Probando extracción de datos técnicos para {simbolo}")
    print(f"URL: {url_prueba}")
    
    # Probar función específica
    print("\n=== Datos extraídos con función específica ===")
    datos_especificos = extraer_datos_tecnicos_especificos(url_prueba)
    for clave, valor in datos_especificos.items():
        print(f"{clave}: {valor}")
    
    # Probar función general
    print("\n=== Datos extraídos con función general ===")
    datos_generales = obtener_datos_tecnicos(url_prueba)
    for clave, valor in datos_generales.items():
        print(f"{clave}: {valor}")
    
    # Probar función básica
    print("\n=== Datos extraídos con función básica ===")
    datos_basicos = obtener_datos_basicos_bono(url_prueba)
    for clave, valor in datos_basicos.items():
        print(f"{clave}: {valor}")
    
    return {
        'especificos': datos_especificos,
        'generales': datos_generales,
        'basicos': datos_basicos
    }

# --- Interfaz para análisis de flujos y TIR ---
st.write("## Análisis de Flujos de Fondos y TIR")

# Mostrar mapeo de categorías
st.write("### Mapeo de Categorías de Scraping")
categorias_disponibles = obtener_categorias_disponibles()

# Crear DataFrame con el mapeo
mapeo_data = []
for categoria in categorias_disponibles:
    bonos_categoria = obtener_bonos_por_categoria(categoria)
    mapeo_data.append({
        'Categoría Scraping': categoria,
        'Bonos Disponibles': len(bonos_categoria),
        'Símbolos': ', '.join(bonos_categoria[:5]) + ('...' if len(bonos_categoria) > 5 else ''),
        'Tipos de Bono': ', '.join(set([INSTRUMENTOS_FINANCIEROS.get(s, {}).get('tipo', '') for s in bonos_categoria]))
    })

df_mapeo = pd.DataFrame(mapeo_data)
st.dataframe(df_mapeo, use_container_width=True)

# Análisis por categoría
st.write("### Análisis por Categoría de Scraping")
categoria_seleccionada = st.selectbox(
    "Seleccione una categoría para analizar:",
    categorias_disponibles
)

if st.button("Analizar Categoría"):
    bonos_categoria = obtener_bonos_por_categoria(categoria_seleccionada)
    
    if bonos_categoria:
        st.write(f"#### Analizando {len(bonos_categoria)} bonos de la categoría: {categoria_seleccionada}")
        
        with st.spinner(f"Analizando {len(bonos_categoria)} bonos..."):
            bearer_token = None
            if 'token_portador' in st.session_state:
                bearer_token = st.session_state['token_portador']
            
            resultados = analizar_panel_bonos(bonos_categoria, bearer_token)
            
            if resultados:
                # Crear DataFrame de resultados
                datos_resultados = []
                for simbolo, resultado in resultados.items():
                    datos_resultados.append({
                        'Símbolo': simbolo,
                        'Nombre': resultado['info'].get('nombre', ''),
                        'Precio': resultado['precio'],
                        'TIR (%)': resultado['tir'],
                        'Vencimiento': resultado['info'].get('vencimiento', ''),
                        'Tipo': resultado['info'].get('tipo', ''),
                        'Decreto': resultado['info'].get('decreto', ''),
                        'Error': resultado.get('error', '')
                    })
                
                df_resultados = pd.DataFrame(datos_resultados)
                st.write("#### Resultados del Análisis:")
                st.dataframe(df_resultados, use_container_width=True)
                
                # Gráfico de TIR por bono
                df_con_tir = df_resultados[df_resultados['TIR (%)'].notna()]
                if not df_con_tir.empty:
                    fig_tir = px.bar(
                        df_con_tir,
                        x='Símbolo',
                        y='TIR (%)',
                        title=f'TIR por Bono - Categoría: {categoria_seleccionada}',
                        color='TIR (%)',
                        color_continuous_scale='RdYlGn'
                    )
                    st.plotly_chart(fig_tir, use_container_width=True)
                    
                    # Estadísticas
                    st.write("#### Estadísticas:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("TIR Promedio", f"{df_con_tir['TIR (%)'].mean():.2f}%")
                    with col2:
                        st.metric("TIR Máxima", f"{df_con_tir['TIR (%)'].max():.2f}%")
                    with col3:
                        st.metric("TIR Mínima", f"{df_con_tir['TIR (%)'].min():.2f}%")
            else:
                st.warning("No se pudieron obtener resultados para esta categoría")
    else:
        st.warning(f"No hay bonos disponibles para la categoría: {categoria_seleccionada}")

# Selección de bonos
bonos_disponibles = list(INSTRUMENTOS_FINANCIEROS.keys())
bonos_seleccionados = st.multiselect(
    "Seleccione bonos para analizar:",
    bonos_disponibles,
    default=["AE38D", "AE35D", "BONCER2025"]
)

# Botón para analizar
if st.button("Analizar Flujos y TIR"):
    if not bonos_seleccionados:
        st.warning("Seleccione al menos un bono")
    else:
        with st.spinner("Calculando flujos y TIR..."):
            # Verificar autenticación
            bearer_token = None
            if 'token_portador' in st.session_state:
                bearer_token = st.session_state['token_portador']
            
            # Analizar cada bono
            for simbolo in bonos_seleccionados:
                st.write(f"### Análisis de {simbolo}")
                
                flujo, tir, error = calcular_flujo_y_tir(simbolo, bearer_token)
                
                if error:
                    st.error(f"Error: {error}")
                    continue
                
                precio_actual = obtener_precio_actual(simbolo, bearer_token)
                bono_info = INSTRUMENTOS_FINANCIEROS[simbolo]
                
                # Mostrar información del bono
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Precio Actual", f"${precio_actual:.2f}" if precio_actual else "N/A")
                with col2:
                    st.metric("TIR", f"{tir:.2f}%" if tir else "N/A")
                with col3:
                    st.metric("Vencimiento", bono_info['vencimiento'])
                
                # Mostrar flujo de fondos
                if flujo is not None:
                    st.write("#### Flujo de Fondos:")
                    st.dataframe(flujo, use_container_width=True)
                    
                    # Mostrar información detallada del cálculo
                    if tir is not None:
                        st.write("#### Información del Cálculo de TIR:")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("TIR Calculada", f"{tir:.2f}%")
                        with col2:
                            if 'info_adicional' in locals() and 'anos_hasta_vencimiento' in info_adicional:
                                st.metric("Años hasta Vencimiento", f"{info_adicional['anos_hasta_vencimiento']:.2f}")
                        with col3:
                            if 'info_adicional' in locals() and 'valor_presente_flujos' in info_adicional:
                                st.metric("Valor Presente Flujos", f"${info_adicional['valor_presente_flujos']:.2f}")
                    
                    # Graficar
                    fig = graficar_flujo_y_tir(simbolo, flujo, tir, precio_actual)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                st.write("---")

# Análisis de panel completo
st.write("### Análisis de Panel Completo")

paneles_predefinidos = {
    "Bonos STEP UP USD": ["AE30D", "AE35D", "AE38D", "AE41D", "AE46D"],
    "Bonos STEP UP EUR": ["AE30E", "AE35E", "AE38E", "AE41E", "AE46E"],
    "Bonos REP USD": ["AR30D", "AR35D", "AR38D", "AR41D"],
    "BONCER": ["BONCER2025", "BONCER2025AGO", "BONCER2025JUN", "BONCER2031"],
    "BONTES": ["BONTE2026", "BONTE2027", "BONTE2030", "BONTE2031"]
}

panel_seleccionado = st.selectbox(
    "Seleccione un panel predefinido:",
    list(paneles_predefinidos.keys())
)

if st.button("Analizar Panel"):
    bonos_panel = paneles_predefinidos[panel_seleccionado]
    
    with st.spinner(f"Analizando panel {panel_seleccionado}..."):
        bearer_token = None
        if 'token_portador' in st.session_state:
            bearer_token = st.session_state['token_portador']
        
        resultados = analizar_panel_bonos(bonos_panel, bearer_token)
        
        if resultados:
            # Crear DataFrame de resultados
            datos_resultados = []
            for simbolo, resultado in resultados.items():
                datos_resultados.append({
                    'Símbolo': simbolo,
                    'Nombre': resultado['info']['nombre'],
                    'Precio': resultado['precio'],
                    'TIR (%)': resultado['tir'],
                    'Vencimiento': resultado['info']['vencimiento'],
                    'Tipo': resultado['info']['tipo']
                })
            
            df_resultados = pd.DataFrame(datos_resultados)
            st.write("#### Resultados del Panel:")
            st.dataframe(df_resultados, use_container_width=True)
            
            # Gráfico de TIR por bono
            if any(r['tir'] for r in resultados.values()):
                fig_tir = px.bar(
                    df_resultados,
                    x='Símbolo',
                    y='TIR (%)',
                    title=f'TIR por Bono - Panel {panel_seleccionado}',
                    color='TIR (%)',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_tir, use_container_width=True)
        else:
            st.warning("No se pudieron obtener resultados para el panel")

# --- Sección opcional de autenticación para series históricas ---
st.write("---")
st.write("## Autenticación IOL (Opcional - para series históricas)")

# Crear sidebar para autenticación
with st.sidebar:
    st.write("### Credenciales IOL")
    usuario = st.text_input("Usuario", key="usuario_iol")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_iol")
    autenticar = st.button("Autenticar", key="autenticar_iol")
    
    if autenticar and usuario and contrasena:
        token_portador, token_refresco = obtener_tokens(usuario, contrasena)
        if token_portador:
            st.session_state['token_portador'] = token_portador
            st.session_state['token_refresco'] = token_refresco
            st.success("Autenticación exitosa.")
        else:
            st.error("Error en la autenticación.")
    
    # Mostrar estado de autenticación
    if 'token_portador' in st.session_state and st.session_state['token_portador']:
        st.success("✅ Autenticado")
    else:
        st.info("❌ No autenticado")

# --- Funciones para cálculo de flujos y TIR ---

def obtener_precio_actual(simbolo, bearer_token):
    """
    Obtiene el precio actual del bono desde la API de IOL
    """
    try:
        if not bearer_token:
            return None
        
        # Endpoint para cotización actual
        url = f"https://api.invertironline.com/api/v2/BCBA/Titulos/{simbolo}/Cotizacion"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {bearer_token}'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'ultimoPrecio' in data:
                return float(data['ultimoPrecio'])
            elif 'precio' in data:
                return float(data['precio'])
        
        return None
        
    except Exception as e:
        print(f"Error obteniendo precio de {simbolo}: {str(e)}")
        return None

def calcular_tir_numerica(flujo_df, precio_actual):
    """
    Calcula la TIR usando método numérico basado en flujos reales
    """
    try:
        if flujo_df.empty:
            return None
        
        # Convertir fechas a días desde hoy
        hoy = pd.Timestamp.today()
        flujo_df['dias'] = (flujo_df['fecha'] - hoy).dt.days
        
        # Filtrar flujos futuros
        flujo_futuro = flujo_df[flujo_df['dias'] > 0].copy()
        
        if flujo_futuro.empty:
            return None
        
        # Método de bisección para encontrar TIR
        def npv(tasa):
            npv_total = -precio_actual
            for _, row in flujo_futuro.iterrows():
                flujo = row['flujo']
                dias = row['dias']
                if dias > 0:
                    npv_total += flujo / ((1 + tasa) ** (dias / 365.25))
            return npv_total
        
        # Buscar TIR entre -50% y 200% para cubrir casos extremos
        tasa_baja = -0.5
        tasa_alta = 2.0
        
        # Verificar que hay cambio de signo
        npv_baja = npv(tasa_baja)
        npv_alta = npv(tasa_alta)
        
        if npv_baja * npv_alta > 0:
            # No hay cambio de signo, intentar con otros rangos
            tasa_baja = 0.0
            tasa_alta = 1.0
            npv_baja = npv(tasa_baja)
            npv_alta = npv(tasa_alta)
            
            if npv_baja * npv_alta > 0:
                return None  # No se puede calcular TIR
        
        # Método de bisección mejorado
        for _ in range(100):  # Más iteraciones para mejor precisión
            tasa_media = (tasa_baja + tasa_alta) / 2
            npv_media = npv(tasa_media)
            
            if abs(npv_media) < 0.001:  # Mayor precisión
                return tasa_media * 100
            
            if npv_media > 0:
                tasa_baja = tasa_media
            else:
                tasa_alta = tasa_media
        
        # Retornar el promedio final
        return (tasa_baja + tasa_alta) / 2 * 100
        
    except Exception as e:
        print(f"Error calculando TIR: {str(e)}")
        return None

def calcular_flujo_step_up(bono_info):
    """
    Calcula flujo para bonos STEP UP usando datos reales
    """
    try:
        fecha_emision = parse(bono_info['fecha_emision'], dayfirst=True)
        fecha_vencimiento = parse(bono_info['vencimiento'], dayfirst=True)
        tasas_texto = bono_info['tasa_interes']
        
        # Extraer tasas del texto usando regex más preciso
        import re
        # Buscar tasas con formato: 0,125% - 0,50% - 0,75% - 1,75%
        tasas = re.findall(r'(\d+[\.,]?\d*)\s*%', tasas_texto)
        tasas = [float(t.replace(',', '.'))/100 for t in tasas]
        
        if not tasas:
            # Si no se encuentran tasas, usar tasa única
            tasa_match = re.search(r'(\d+[\.,]?\d*)', tasas_texto)
            if tasa_match:
                tasa = float(tasa_match.group(1).replace(',', '.'))/100
                tasas = [tasa]
        
        # Calcular fechas de pago semestrales
        flujos = []
        fechas = []
        
        # Determinar frecuencia de pagos (semestral para STEP UP)
        frecuencia_pagos = 2  # semestral
        
        # Calcular número de pagos
        dias_total = (fecha_vencimiento - fecha_emision).days
        pagos_por_ano = frecuencia_pagos
        total_pagos = int((dias_total / 365.25) * pagos_por_ano)
        
        # Distribuir tasas a lo largo del período
        if len(tasas) == 1:
            # Una sola tasa
            tasa_actual = tasas[0]
            for i in range(total_pagos):
                fecha_pago = fecha_emision + pd.DateOffset(months=6 * (i + 1))
                if fecha_pago <= fecha_vencimiento:
                    cupon = 100 * tasa_actual / frecuencia_pagos
                    flujos.append(cupon)
                    fechas.append(fecha_pago)
        else:
            # Múltiples tasas (STEP UP real)
            pagos_por_tasa = total_pagos // len(tasas)
            pagos_restantes = total_pagos % len(tasas)
            
            pago_actual = 0
            for i, tasa in enumerate(tasas):
                pagos_esta_tasa = pagos_por_tasa + (1 if i < pagos_restantes else 0)
                
                for j in range(pagos_esta_tasa):
                    fecha_pago = fecha_emision + pd.DateOffset(months=6 * (pago_actual + 1))
                    if fecha_pago <= fecha_vencimiento:
                        cupon = 100 * tasa / frecuencia_pagos
                        flujos.append(cupon)
                        fechas.append(fecha_pago)
                        pago_actual += 1
        
        # Último pago incluye capital
        if flujos:
            flujos[-1] += 100
        
        return pd.DataFrame({'fecha': fechas, 'flujo': flujos})
        
    except Exception as e:
        print(f"Error en flujo STEP UP: {str(e)}")
        return None

def calcular_flujo_boncer(bono_info):
    """
    Calcula flujo para bonos CER usando datos reales
    """
    try:
        fecha_emision = parse(bono_info['fecha_emision'], dayfirst=True)
        fecha_vencimiento = parse(bono_info['vencimiento'], dayfirst=True)
        tasa_texto = bono_info['tasa_interes']
        
        # Extraer tasa con regex más preciso
        import re
        tasa_match = re.search(r'(\d+[\.,]?\d*)\s*%', tasa_texto)
        if tasa_match:
            tasa = float(tasa_match.group(1).replace(',', '.')) / 100
        else:
            # Buscar cualquier número que pueda ser tasa
            tasa_match = re.search(r'(\d+[\.,]?\d*)', tasa_texto)
            if tasa_match:
                tasa = float(tasa_match.group(1).replace(',', '.')) / 100
            else:
                tasa = 0.0
        
        # Calcular pagos semestrales
        dias_total = (fecha_vencimiento - fecha_emision).days
        pagos_semestrales = max(1, int(dias_total / 180))
        
        flujos = []
        fechas = []
        
        # Para bonos CER, los pagos son semestrales
        for i in range(pagos_semestrales):
            fecha_pago = fecha_emision + pd.DateOffset(months=6 * (i + 1))
            if fecha_pago <= fecha_vencimiento:
                # Cupón semestral
                cupon = 100 * tasa / 2
                flujos.append(cupon)
                fechas.append(fecha_pago)
        
        # Último pago incluye capital
        if flujos:
            flujos[-1] += 100
        
        # Si no hay flujos, crear al menos el pago final
        if not flujos:
            flujos.append(100)
            fechas.append(fecha_vencimiento)
        
        return pd.DataFrame({'fecha': fechas, 'flujo': flujos})
        
    except Exception as e:
        print(f"Error en flujo BONCER: {str(e)}")
        return None

def calcular_flujo_bullet(bono_info):
    """
    Calcula flujo para bonos bullet (todo al final)
    """
    try:
        fecha_emision = parse(bono_info['fecha_emision'], dayfirst=True)
        fecha_vencimiento = parse(bono_info['vencimiento'], dayfirst=True)
        tasa_texto = bono_info['tasa_interes']
        
        # Extraer tasa
        import re
        tasa_match = re.search(r'(\d+[\.,]?\d*)', tasa_texto)
        if tasa_match:
            tasa = float(tasa_match.group(1).replace(',', '.')) / 100
        else:
            tasa = 0.0
        
        # Pago único al vencimiento
        pago_final = 100 * (1 + tasa)
        
        return pd.DataFrame({
            'fecha': [fecha_vencimiento],
            'flujo': [pago_final]
        })
        
    except Exception as e:
        print(f"Error en flujo bullet: {str(e)}")
        return None

def calcular_flujo_tasa_fija(bono_info):
    """
    Calcula flujo para bonos con tasa fija
    """
    try:
        fecha_emision = parse(bono_info['fecha_emision'], dayfirst=True)
        fecha_vencimiento = parse(bono_info['vencimiento'], dayfirst=True)
        tasa_texto = bono_info['tasa_interes']
        
        # Extraer tasa
        import re
        tasa_match = re.search(r'(\d+[\.,]?\d*)', tasa_texto)
        if tasa_match:
            tasa = float(tasa_match.group(1).replace(',', '.')) / 100
        else:
            tasa = 0.0
        
        # Calcular pagos semestrales
        dias_total = (fecha_vencimiento - fecha_emision).days
        pagos_semestrales = max(1, int(dias_total / 180))
        
        flujos = []
        fechas = []
        
        for i in range(pagos_semestrales):
            fecha_pago = fecha_emision + pd.DateOffset(months=6 * (i + 1))
            if fecha_pago <= fecha_vencimiento:
                cupon = 100 * tasa / 2
                flujos.append(cupon)
                fechas.append(fecha_pago)
        
        # Último pago incluye capital
        if flujos:
            flujos[-1] += 100
        
        return pd.DataFrame({'fecha': fechas, 'flujo': flujos})
        
    except Exception as e:
        print(f"Error en flujo tasa fija: {str(e)}")
        return None

def calcular_flujo_pbi_linked(bono_info):
    """
    Calcula flujo para bonos vinculados al PBI
    """
    try:
        fecha_emision = parse(bono_info['fecha_emision'], dayfirst=True)
        fecha_vencimiento = parse(bono_info['vencimiento'], dayfirst=True)
        
        # Para bonos PBI, asumir cupón variable
        dias_total = (fecha_vencimiento - fecha_emision).days
        pagos_anuales = max(1, int(dias_total / 365))
        
        flujos = []
        fechas = []
        
        for i in range(pagos_anuales):
            fecha_pago = fecha_emision + pd.DateOffset(years=i + 1)
            if fecha_pago <= fecha_vencimiento:
                # Cupón variable según PBI (simulado)
                cupon = 100 * 0.02  # 2% anual aproximado
                flujos.append(cupon)
                fechas.append(fecha_pago)
        
        # Último pago incluye capital
        if flujos:
            flujos[-1] += 100
        
        return pd.DataFrame({'fecha': fechas, 'flujo': flujos})
        
    except Exception as e:
        print(f"Error en flujo PBI: {str(e)}")
        return None

def calcular_flujo_segun_tipo(bono_info):
    """
    Calcula el flujo de fondos según el tipo de bono
    """
    try:
        tipo_bono = bono_info['tipo']
        fecha_emision = parse(bono_info['fecha_emision'], dayfirst=True)
        fecha_vencimiento = parse(bono_info['vencimiento'], dayfirst=True)
        tasa_interes = bono_info['tasa_interes']
        moneda = bono_info['moneda']
        
        if tipo_bono == "STEP_UP":
            return calcular_flujo_step_up(bono_info)
        elif tipo_bono == "BONCER":
            return calcular_flujo_boncer(bono_info)
        elif tipo_bono in ["PAR", "DESCUENTO", "CUASIPAR"]:
            return calcular_flujo_bullet(bono_info)
        elif tipo_bono in ["BONAR", "BONTE", "BONCAP", "BONAD_DUAL", "BONTE_DLK", "BOCON"]:
            return calcular_flujo_tasa_fija(bono_info)
        elif tipo_bono == "PBI_LINKED":
            return calcular_flujo_pbi_linked(bono_info)
        else:
            return calcular_flujo_bullet(bono_info)  # Por defecto
            
    except Exception as e:
        print(f"Error calculando flujo para tipo {bono_info.get('tipo')}: {str(e)}")
        return None

def calcular_flujo_y_tir(simbolo, bearer_token=None):
    """
    Calcula el flujo de fondos y TIR para un bono específico usando datos reales
    """
    try:
        if simbolo not in INSTRUMENTOS_FINANCIEROS:
            return None, None, f"Bono {simbolo} no encontrado en la base de datos"
        
        bono_info = INSTRUMENTOS_FINANCIEROS[simbolo]
        
        # Obtener precio actual si hay token
        precio_actual = None
        if bearer_token:
            precio_actual = obtener_precio_actual(simbolo, bearer_token)
        
        # Si no hay precio actual, usar precio nominal
        if not precio_actual:
            precio_actual = 100.0
        
        # Calcular flujo según tipo de bono usando datos reales
        flujo_df = calcular_flujo_segun_tipo(bono_info)
        
        if flujo_df is None or flujo_df.empty:
            return None, None, "No se pudo calcular el flujo de fondos"
        
        # Verificar que hay flujos futuros
        hoy = pd.Timestamp.today()
        flujo_df['dias'] = (flujo_df['fecha'] - hoy).dt.days
        flujos_futuros = flujo_df[flujo_df['dias'] > 0]
        
        if flujos_futuros.empty:
            return flujo_df, None, "No hay flujos futuros para calcular TIR"
        
        # Calcular TIR usando método numérico mejorado
        tir = calcular_tir_numerica(flujo_df, precio_actual)
        
        # Validar que la TIR sea razonable
        if tir is not None and (tir < -50 or tir > 200):
            print(f"TIR fuera de rango para {simbolo}: {tir}%")
            tir = None
        
        return flujo_df, tir, None
        
    except Exception as e:
        return None, None, f"Error calculando flujo y TIR: {str(e)}"

def graficar_flujo_y_tir(simbolo, flujo_df, tir, precio_actual):
    """
    Crea gráfico del flujo de fondos y TIR
    """
    try:
        if flujo_df is None or flujo_df.empty:
            return None
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Flujo de Fondos', 'Evolución Temporal'),
            vertical_spacing=0.1
        )
        
        # Gráfico de barras para flujo de fondos
        fig.add_trace(
            go.Bar(
                x=flujo_df['fecha'],
                y=flujo_df['flujo'],
                name='Flujo de Fondos',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        # Gráfico de línea para evolución temporal
        fig.add_trace(
            go.Scatter(
                x=flujo_df['fecha'],
                y=flujo_df['flujo'].cumsum(),
                name='Flujo Acumulado',
                line=dict(color='red')
            ),
            row=2, col=1
        )
        
        # Actualizar layout
        fig.update_layout(
            title=f'Análisis de {simbolo} - TIR: {tir:.2f}% - Precio: ${precio_actual:.2f}' if precio_actual else f'Análisis de {simbolo} - TIR: {tir:.2f}%',
            height=600,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfico: {str(e)}")
        return None

def analizar_panel_bonos(bonos_lista, bearer_token):
    """
    Analiza un panel completo de bonos usando flujos reales
    """
    resultados = {}
    
    for simbolo in bonos_lista:
        try:
            # Calcular flujo y TIR usando datos reales
            flujo, tir, error = calcular_flujo_y_tir(simbolo, bearer_token)
            precio = obtener_precio_actual(simbolo, bearer_token)
            
            # Calcular información adicional
            info_adicional = {}
            if flujo is not None and not flujo.empty:
                # Calcular años hasta vencimiento
                hoy = pd.Timestamp.today()
                fecha_vencimiento = flujo['fecha'].max()
                anos_hasta_vencimiento = (fecha_vencimiento - hoy).days / 365.25
                info_adicional['anos_hasta_vencimiento'] = anos_hasta_vencimiento
                
                # Calcular valor presente de flujos
                if precio and tir:
                    flujos_futuros = flujo[flujo['dias'] > 0]
                    vp_flujos = sum(
                        flujo_valor / ((1 + tir/100) ** (dias / 365.25))
                        for flujo_valor, dias in zip(flujos_futuros['flujo'], flujos_futuros['dias'])
                    )
                    info_adicional['valor_presente_flujos'] = vp_flujos
                    info_adicional['precio_teorico'] = vp_flujos
            
            resultados[simbolo] = {
                'flujo': flujo,
                'tir': tir,
                'precio': precio,
                'info': INSTRUMENTOS_FINANCIEROS.get(simbolo, {}),
                'error': error,
                'info_adicional': info_adicional
            }
            
        except Exception as e:
            resultados[simbolo] = {
                'flujo': None,
                'tir': None,
                'precio': None,
                'info': INSTRUMENTOS_FINANCIEROS.get(simbolo, {}),
                'error': str(e),
                'info_adicional': {}
            }
    
    return resultados

def calcular_paridad(simbolo, datos_tecnicos, precio_actual):
    """Calcula la paridad del bono usando datos reales"""
    try:
        if not precio_actual:
            return None
        
        # Buscar valor nominal en datos técnicos
        valor_nominal = None
        
        # Buscar en campos específicos de datos técnicos
        campos_nominal = ['Monto nominal vigente en la moneda original de emisión', 
                         'Monto residual en la moneda original de emisión',
                         'Valor nominal', 'Nominal', 'Valor']
        
        for campo in campos_nominal:
            if campo in datos_tecnicos:
                try:
                    valor_texto = datos_tecnicos[campo]
                    # Extraer número del texto
                    import re
                    numeros = re.findall(r'[\d,\.]+', str(valor_texto))
                    if numeros:
                        valor_nominal = float(numeros[0].replace(',', ''))
                        break
                except:
                    continue
        
        # Si no se encuentra en campos específicos, buscar en cualquier campo
        if not valor_nominal:
            for key, value in datos_tecnicos.items():
                if 'nominal' in key.lower() or 'valor' in key.lower():
                    try:
                        # Extraer número del texto
                        import re
                        numeros = re.findall(r'[\d,\.]+', str(value))
                        if numeros:
                            valor_nominal = float(numeros[0].replace(',', ''))
                            break
                    except:
                        continue
        
        # Si no se encuentra valor nominal, usar 100 como valor estándar
        if not valor_nominal:
            valor_nominal = 100.0
        
        # Calcular paridad
        paridad = (precio_actual / valor_nominal) * 100
        
        # Validar que la paridad sea razonable
        if paridad < 0 or paridad > 1000:
            print(f"Paridad fuera de rango para {simbolo}: {paridad}%")
            return None
        
        return paridad
        
    except Exception as e:
        print(f"Error calculando paridad: {str(e)}")
        return None

def calcular_tir_bono(simbolo, datos_tecnicos, precio_actual):
    """Calcula la TIR del bono usando flujos reales"""
    try:
        # Usar la función principal que calcula flujos reales
        if simbolo in INSTRUMENTOS_FINANCIEROS:
            flujo, tir, error = calcular_flujo_y_tir(simbolo, None)
            return tir
        else:
            # Para bonos no en la base de datos, calcular TIR aproximada
            if not precio_actual:
                return None
            
            # Buscar tasa de interés en datos técnicos
            tasa_interes = None
            campos_tasa = ['Interés', 'Tasa de interés', 'Tasa', 'Cupón']
            
            for campo in campos_tasa:
                if campo in datos_tecnicos:
                    try:
                        import re
                        tasas = re.findall(r'(\d+[\.,]?\d*)\s*%', datos_tecnicos[campo])
                        if tasas:
                            tasa_interes = float(tasas[0].replace(',', '')) / 100
                            break
                    except:
                        continue
            
            # Si no se encuentra en campos específicos, buscar en cualquier campo
            if not tasa_interes:
                for key, value in datos_tecnicos.items():
                    if 'interés' in key.lower() or 'tasa' in key.lower():
                        try:
                            import re
                            tasas = re.findall(r'(\d+[\.,]?\d*)\s*%', str(value))
                            if tasas:
                                tasa_interes = float(tasas[0].replace(',', '')) / 100
                                break
                        except:
                            continue
            
            if tasa_interes:
                # TIR aproximada basada en precio y tasa
                # Si el precio está por debajo del nominal, TIR > tasa
                # Si el precio está por encima del nominal, TIR < tasa
                valor_nominal = 100.0
                if precio_actual < valor_nominal:
                    # Bono bajo la par, TIR mayor que la tasa
                    spread_estimado = ((valor_nominal - precio_actual) / valor_nominal) * 10
                    tir_aproximada = tasa_interes * 100 + spread_estimado
                else:
                    # Bono sobre la par, TIR menor que la tasa
                    spread_estimado = ((precio_actual - valor_nominal) / valor_nominal) * 5
                    tir_aproximada = max(0, tasa_interes * 100 - spread_estimado)
                
                return tir_aproximada
            
            return None
            
    except Exception as e:
        print(f"Error calculando TIR: {str(e)}")
        return None

def calcular_paridad_tir_historica(serie_historica, simbolo):
    """Calcula paridad y TIR históricas para una serie"""
    try:
        if serie_historica.empty:
            return serie_historica
        
        # Obtener datos del bono
        bono_info = INSTRUMENTOS_FINANCIEROS.get(simbolo, {})
        
        # Calcular paridad histórica
        valor_nominal = 100.0  # Valor por defecto
        serie_historica['paridad'] = (serie_historica['ultimoPrecio'] / valor_nominal) * 100
        
        # Calcular TIR histórica aproximada
        tasa_interes = 0.05  # 5% por defecto
        if bono_info:
            tasa_texto = bono_info.get('tasa_interes', '')
            import re
            tasas = re.findall(r'[\d,\.]+', tasa_texto)
            if tasas:
                tasa_interes = float(tasas[0].replace(',', '')) / 100
        
        # TIR aproximada basada en precio y tasa
        serie_historica['tir'] = (tasa_interes * 100) + ((100 - serie_historica['ultimoPrecio']) / 100) * 10
        
        return serie_historica
        
    except Exception as e:
        print(f"Error calculando paridad/TIR histórica: {str(e)}")
        return serie_historica

def calcular_ganancias_acumuladas(flujo_df, monto_inversion):
    """Calcula las ganancias acumuladas para un flujo de fondos"""
    try:
        if flujo_df.empty:
            return flujo_df
        
        # Calcular flujos proporcionales al monto de inversión
        flujo_df['flujo_proporcional'] = flujo_df['flujo'] * (monto_inversion / 100)
        
        # Calcular ganancia acumulada
        flujo_df['ganancia_acumulada'] = flujo_df['flujo_proporcional'].cumsum()
        
        return flujo_df
        
    except Exception as e:
        print(f"Error calculando ganancias acumuladas: {str(e)}")
        return flujo_df

# --- Función para mapear tickers de IOL a datos técnicos internos ---
def mapear_tickers_a_datos_tecnicos(tickers_extraidos, base_datos):
    """
    Asocia cada ticker extraído del panel de IOL a su dato técnico fijo de la base interna.
    Si no hay match exacto, intenta un match parcial ignorando sufijos comunes.
    """
    asociacion = {}
    for ticker in tickers_extraidos:
        if ticker in base_datos:
            asociacion[ticker] = base_datos[ticker]
        else:
            # Intentar match parcial (por ejemplo, quitar sufijos como C, D, etc.)
            base_ticker = ticker.rstrip("CD")  # Ajusta según los sufijos posibles
            encontrado = False
            for simbolo in base_datos:
                if simbolo.startswith(base_ticker):
                    asociacion[ticker] = base_datos[simbolo]
                    encontrado = True
                    break
            if not encontrado:
                asociacion[ticker] = None  # No encontrado
    return asociacion

# --- Sistema completo de análisis de bonos ---
st.write("## Sistema de Análisis Completo de Bonos Argentinos")

# Crear tabs para diferentes funcionalidades
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Datos Técnicos y TIR", 
    "📈 Series Históricas", 
    "💰 Simulación de Flujos",
    "🔍 Análisis por Categorías"
])

with tab1:
    st.write("### Obtención de Tickers y Cálculo de Datos Técnicos")
    
    # Selección de panel
    panel_seleccionado = st.selectbox(
        "Seleccione el panel de bonos:",
        list(urls.keys()),
        key="panel_analisis"
    )
    
    if st.button("Obtener Tickers y Calcular Datos", key="obtener_tickers"):
        with st.spinner("Obteniendo tickers y calculando datos técnicos..."):
            # Obtener tickers del panel
            url_panel = urls[panel_seleccionado]
            df_panel = obtener_tabla(url_panel)
            
            if not df_panel.empty and "Error" not in df_panel.columns:
                # Extraer símbolos de la tabla
                simbolos_panel = []
                if len(df_panel.columns) > 0:
                    # Buscar columna con símbolos (primera columna típicamente)
                    simbolos_col = df_panel.iloc[:, 0]
                    simbolos_panel = [str(s).strip() for s in simbolos_col if pd.notna(s) and str(s).strip()]
                
                st.write(f"**Total de tickers encontrados:** {len(simbolos_panel)}")
                
                # Filtrar activos con datos técnicos disponibles
                st.write("### Filtrando activos con datos técnicos disponibles...")
                activos_con_datos = {}
                bearer_token = st.session_state.get('token_portador')
                
                # Procesar todos los símbolos para encontrar los que tienen datos
                for i, simbolo in enumerate(simbolos_panel):
                    try:
                        # Construir URL de fundamentales
                        url_fundamentales = construir_url_fundamentales(simbolo, df_panel)
                        
                        # Obtener datos técnicos
                        datos_tecnicos = obtener_datos_tecnicos(url_fundamentales)
                        
                        if datos_tecnicos and len(datos_tecnicos) > 3:  # Al menos 3 campos de datos
                            # Calcular TIR y paridad
                            precio_actual = obtener_precio_actual(simbolo, bearer_token)
                            paridad = calcular_paridad(simbolo, datos_tecnicos, precio_actual)
                            tir = calcular_tir_bono(simbolo, datos_tecnicos, precio_actual)
                            
                            # Solo incluir si tenemos datos válidos
                            if precio_actual and tir:
                                activos_con_datos[simbolo] = {
                                    'datos_tecnicos': datos_tecnicos,
                                    'precio_actual': precio_actual,
                                    'paridad': paridad,
                                    'tir': tir,
                                    'campos_disponibles': len(datos_tecnicos)
                                }
                                
                                st.write(f"✅ {simbolo}: {len(datos_tecnicos)} campos, TIR: {tir:.2f}%")
                            
                    except Exception as e:
                        continue
                
                st.write(f"**Activos con datos técnicos válidos:** {len(activos_con_datos)}")
                
                # Mostrar resultados si hay datos válidos
                if activos_con_datos:
                    st.write("### Resultados del Análisis")
                    
                    # Crear DataFrame de resultados
                    resultados_data = []
                    for simbolo, datos in activos_con_datos.items():
                        # Obtener fecha de vencimiento si está disponible
                        fecha_vencimiento = datos['datos_tecnicos'].get('Fecha Vencimiento', '')
                        if fecha_vencimiento:
                            try:
                                fecha_venc = parse(fecha_vencimiento, dayfirst=True)
                                dias_hasta_vencimiento = (fecha_venc - pd.Timestamp.now()).days
                            except:
                                dias_hasta_vencimiento = None
                        else:
                            dias_hasta_vencimiento = None
                        
                        resultados_data.append({
                            'Símbolo': simbolo,
                            'Precio Actual': datos['precio_actual'],
                            'Paridad (%)': datos['paridad'],
                            'TIR (%)': datos['tir'],
                            'Días hasta Vencimiento': dias_hasta_vencimiento,
                            'Campos Disponibles': datos['campos_disponibles'],
                            'Emisor': datos['datos_tecnicos'].get('Emisor', ''),
                            'Vencimiento': fecha_vencimiento,
                            'Tasa': datos['datos_tecnicos'].get('Interés', '')
                        })
                    
                    df_resultados = pd.DataFrame(resultados_data)
                    
                    # Ordenar por TIR para mejor visualización
                    df_resultados = df_resultados.sort_values('TIR (%)', ascending=False)
                    
                    st.dataframe(df_resultados, use_container_width=True)
                    
                    # Gráficos comparativos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if any(d['tir'] for d in activos_con_datos.values()):
                            fig_tir = px.bar(
                                df_resultados,
                                x='Símbolo',
                                y='TIR (%)',
                                title='TIR por Bono',
                                color='TIR (%)',
                                color_continuous_scale='RdYlGn'
                            )
                            fig_tir.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_tir, use_container_width=True)
                    
                    with col2:
                        if any(d['paridad'] for d in activos_con_datos.values()):
                            fig_paridad = px.bar(
                                df_resultados,
                                x='Símbolo',
                                y='Paridad (%)',
                                title='Paridad por Bono',
                                color='Paridad (%)',
                                color_continuous_scale='Blues'
                            )
                            fig_paridad.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_paridad, use_container_width=True)
                    
                    # Curva de TIR
                    st.write("### Curva de TIR")
                    
                    # Filtrar datos con días hasta vencimiento válidos
                    df_curva = df_resultados[df_resultados['Días hasta Vencimiento'].notna()].copy()
                    
                    if not df_curva.empty:
                        # Convertir días a años para el eje X
                        df_curva['Años hasta Vencimiento'] = df_curva['Días hasta Vencimiento'] / 365.25
                        
                        # Crear curva de TIR
                        fig_curva = px.scatter(
                            df_curva,
                            x='Años hasta Vencimiento',
                            y='TIR (%)',
                            title='Curva de TIR',
                            labels={'Años hasta Vencimiento': 'Años hasta Vencimiento', 'TIR (%)': 'TIR (%)'},
                            hover_data=['Símbolo', 'Precio Actual', 'Paridad (%)'],
                            color='TIR (%)',
                            color_continuous_scale='RdYlGn'
                        )
                        
                        # Agregar línea de tendencia
                        fig_curva.add_trace(
                            go.Scatter(
                                x=df_curva['Años hasta Vencimiento'],
                                y=df_curva['TIR (%)'],
                                mode='lines',
                                name='Tendencia',
                                line=dict(color='red', dash='dash')
                            )
                        )
                        
                        st.plotly_chart(fig_curva, use_container_width=True)
                        
                        # Estadísticas de la curva
                        st.write("#### Estadísticas de la Curva de TIR:")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("TIR Promedio", f"{df_curva['TIR (%)'].mean():.2f}%")
                        with col2:
                            st.metric("TIR Máxima", f"{df_curva['TIR (%)'].max():.2f}%")
                        with col3:
                            st.metric("TIR Mínima", f"{df_curva['TIR (%)'].min():.2f}%")
                        with col4:
                            st.metric("Activos Analizados", f"{len(df_curva)}")
                        
                        # Análisis por rangos de vencimiento
                        st.write("#### Análisis por Rangos de Vencimiento:")
                        
                        # Crear rangos de años
                        df_curva['Rango Años'] = pd.cut(
                            df_curva['Años hasta Vencimiento'], 
                            bins=[0, 1, 2, 5, 10, 50], 
                            labels=['< 1 año', '1-2 años', '2-5 años', '5-10 años', '> 10 años']
                        )
                        
                        analisis_rangos = df_curva.groupby('Rango Años')['TIR (%)'].agg(['mean', 'count', 'min', 'max']).round(2)
                        analisis_rangos.columns = ['TIR Promedio (%)', 'Cantidad', 'TIR Mínima (%)', 'TIR Máxima (%)']
                        
                        st.dataframe(analisis_rangos, use_container_width=True)
                        
                        # Gráfico de TIR por rango
                        fig_rangos = px.bar(
                            analisis_rangos.reset_index(),
                            x='Rango Años',
                            y='TIR Promedio (%)',
                            title='TIR Promedio por Rango de Vencimiento',
                            color='TIR Promedio (%)',
                            color_continuous_scale='RdYlGn'
                        )
                        st.plotly_chart(fig_rangos, use_container_width=True)
                        
                    else:
                        st.warning("No hay suficientes datos de vencimiento para crear la curva de TIR")
                    
                    # Exportar datos
                    st.write("### Exportar Datos")
                    csv = df_resultados.to_csv(index=False)
                    st.download_button(
                        label="Descargar CSV",
                        data=csv,
                        file_name=f"analisis_bonos_{panel_seleccionado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                else:
                    st.warning("No se encontraron activos con datos técnicos válidos")
            else:
                st.error("No se pudo obtener la tabla del panel")

with tab2:
    st.write("### Series Históricas - Paridad y TIR")
    
    # Verificar autenticación
    if 'token_portador' not in st.session_state or not st.session_state['token_portador']:
        st.warning("⚠️ Necesita autenticarse para acceder a las series históricas")
        st.write("Use la sección de autenticación en el sidebar")
    else:
        # Selección de bono para análisis histórico
        bono_historico = st.selectbox(
            "Seleccione un bono para análisis histórico:",
            list(INSTRUMENTOS_FINANCIEROS.keys()),
            key="bono_historico"
        )
        
        # Parámetros de fechas
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input(
                "Fecha desde:",
                value=datetime.now() - timedelta(days=365),
                key="fecha_desde_hist"
            )
        with col2:
            fecha_hasta = st.date_input(
                "Fecha hasta:",
                value=datetime.now(),
                key="fecha_hasta_hist"
            )
        
        if st.button("Obtener Series Históricas", key="obtener_historicas"):
            with st.spinner("Obteniendo series históricas..."):
                bearer_token = st.session_state['token_portador']
                
                # Obtener serie histórica
                serie_historica = obtener_serie_historica(
                    bono_historico, 
                    "BCBA", 
                    fecha_desde.strftime('%Y-%m-%d'),
                    fecha_hasta.strftime('%Y-%m-%d'),
                    "true",
                    bearer_token
                )
                
                if not serie_historica.empty:
                    st.write(f"**Serie histórica obtenida:** {len(serie_historica)} registros")
                    
                    # Calcular paridad y TIR históricas
                    serie_historica = calcular_paridad_tir_historica(serie_historica, bono_historico)
                    
                    # Gráficos históricos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de precios
                        fig_precios = px.line(
                            serie_historica,
                            x='fecha',
                            y='ultimoPrecio',
                            title=f'Precio Histórico - {bono_historico}',
                            labels={'ultimoPrecio': 'Precio', 'fecha': 'Fecha'}
                        )
                        st.plotly_chart(fig_precios, use_container_width=True)
                    
                    with col2:
                        # Gráfico de paridad
                        if 'paridad' in serie_historica.columns:
                            fig_paridad = px.line(
                                serie_historica,
                                x='fecha',
                                y='paridad',
                                title=f'Paridad Histórica - {bono_historico}',
                                labels={'paridad': 'Paridad (%)', 'fecha': 'Fecha'}
                            )
                            st.plotly_chart(fig_paridad, use_container_width=True)
                    
                    # Gráfico de TIR histórica
                    if 'tir' in serie_historica.columns:
                        fig_tir = px.line(
                            serie_historica,
                            x='fecha',
                            y='tir',
                            title=f'TIR Histórica - {bono_historico}',
                            labels={'tir': 'TIR (%)', 'fecha': 'Fecha'},
                            color_discrete_sequence=['red']
                        )
                        st.plotly_chart(fig_tir, use_container_width=True)
                    
                    # Estadísticas históricas
                    st.write("### Estadísticas Históricas")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Precio Máximo", f"${serie_historica['ultimoPrecio'].max():.2f}")
                    with col2:
                        st.metric("Precio Mínimo", f"${serie_historica['ultimoPrecio'].min():.2f}")
                    with col3:
                        if 'paridad' in serie_historica.columns:
                            st.metric("Paridad Promedio", f"{serie_historica['paridad'].mean():.2f}%")
                    with col4:
                        if 'tir' in serie_historica.columns:
                            st.metric("TIR Promedio", f"{serie_historica['tir'].mean():.2f}%")
                    
                else:
                    st.warning("No se pudieron obtener series históricas para este bono")

with tab3:
    st.write("### Simulación de Flujos de Fondos")
    
    # Selección de bono para simulación
    bono_simulacion = st.selectbox(
        "Seleccione un bono para simulación:",
        list(INSTRUMENTOS_FINANCIEROS.keys()),
        key="bono_simulacion"
    )
    
    # Parámetros de simulación
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio_sim = st.date_input(
            "Fecha de inicio de simulación:",
            value=datetime.now(),
            key="fecha_inicio_sim"
        )
    with col2:
        monto_inversion = st.number_input(
            "Monto de inversión ($):",
            min_value=1000,
            value=100000,
            step=1000,
            key="monto_inversion"
        )
    
    if st.button("Simular Flujo de Fondos", key="simular_flujo"):
        with st.spinner("Calculando simulación..."):
            # Obtener datos del bono
            bono_info = INSTRUMENTOS_FINANCIEROS[bono_simulacion]
            
            # Calcular flujo de fondos
            flujo_df = calcular_flujo_segun_tipo(bono_info)
            
            if flujo_df is not None:
                # Filtrar flujos futuros desde la fecha de inicio
                fecha_inicio_dt = pd.Timestamp(fecha_inicio_sim)
                flujo_futuro = flujo_df[flujo_df['fecha'] >= fecha_inicio_dt].copy()
                
                if not flujo_futuro.empty:
                    # Calcular ganancias acumuladas
                    flujo_futuro = calcular_ganancias_acumuladas(flujo_futuro, monto_inversion)
                    
                    st.write("### Flujo de Fondos Simulado")
                    st.dataframe(flujo_futuro, use_container_width=True)
                    
                    # Gráficos de simulación
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de flujos individuales
                        fig_flujos = px.bar(
                            flujo_futuro,
                            x='fecha',
                            y='flujo',
                            title='Flujos de Fondos',
                            labels={'flujo': 'Flujo ($)', 'fecha': 'Fecha'}
                        )
                        st.plotly_chart(fig_flujos, use_container_width=True)
                    
                    with col2:
                        # Gráfico de ganancias acumuladas
                        fig_ganancias = px.line(
                            flujo_futuro,
                            x='fecha',
                            y='ganancia_acumulada',
                            title='Ganancias Acumuladas',
                            labels={'ganancia_acumulada': 'Ganancia ($)', 'fecha': 'Fecha'},
                            color_discrete_sequence=['green']
                        )
                        st.plotly_chart(fig_ganancias, use_container_width=True)
                    
                    # Resumen de simulación
                    st.write("### Resumen de Simulación")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        ganancia_total = flujo_futuro['ganancia_acumulada'].iloc[-1] - monto_inversion
                        st.metric("Ganancia Total", f"${ganancia_total:,.2f}")
                    
                    with col2:
                        rendimiento_total = (ganancia_total / monto_inversion) * 100
                        st.metric("Rendimiento Total", f"{rendimiento_total:.2f}%")
                    
                    with col3:
                        plazo_dias = (flujo_futuro['fecha'].iloc[-1] - fecha_inicio_dt).days
                        st.metric("Plazo (días)", f"{plazo_dias}")
                    
                else:
                    st.warning("No hay flujos futuros para la fecha seleccionada")
            else:
                st.error("No se pudo calcular el flujo de fondos para este bono")

with tab4:
    st.write("### Análisis por Categorías de Scraping")
    
    # Mostrar mapeo de categorías
    categorias_disponibles = obtener_categorias_disponibles()
    
    # Crear DataFrame con el mapeo
    mapeo_data = []
    for categoria in categorias_disponibles:
        bonos_categoria = obtener_bonos_por_categoria(categoria)
        mapeo_data.append({
            'Categoría Scraping': categoria,
            'Bonos Disponibles': len(bonos_categoria),
            'Símbolos': ', '.join(bonos_categoria[:5]) + ('...' if len(bonos_categoria) > 5 else ''),
            'Tipos de Bono': ', '.join(set([INSTRUMENTOS_FINANCIEROS.get(s, {}).get('tipo', '') for s in bonos_categoria]))
        })
    
    df_mapeo = pd.DataFrame(mapeo_data)
    st.dataframe(df_mapeo, use_container_width=True)
    
    # Análisis por categoría
    categoria_seleccionada = st.selectbox(
        "Seleccione una categoría para analizar:",
        categorias_disponibles,
        key="categoria_analisis"
    )
    
    if st.button("Analizar Categoría", key="analizar_categoria"):
        bonos_categoria = obtener_bonos_por_categoria(categoria_seleccionada)
        
        if bonos_categoria:
            st.write(f"#### Analizando {len(bonos_categoria)} bonos de la categoría: {categoria_seleccionada}")
            
            with st.spinner(f"Analizando {len(bonos_categoria)} bonos..."):
                bearer_token = st.session_state.get('token_portador')
                
                resultados = analizar_panel_bonos(bonos_categoria, bearer_token)
                
                if resultados:
                    # Crear DataFrame de resultados
                    datos_resultados = []
                    for simbolo, resultado in resultados.items():
                        datos_resultados.append({
                            'Símbolo': simbolo,
                            'Nombre': resultado['info'].get('nombre', ''),
                            'Precio': resultado['precio'],
                            'TIR (%)': resultado['tir'],
                            'Vencimiento': resultado['info'].get('vencimiento', ''),
                            'Tipo': resultado['info'].get('tipo', ''),
                            'Decreto': resultado['info'].get('decreto', ''),
                            'Error': resultado.get('error', '')
                        })
                    
                    df_resultados = pd.DataFrame(datos_resultados)
                    st.write("#### Resultados del Análisis:")
                    st.dataframe(df_resultados, use_container_width=True)
                    
                    # Gráfico de TIR por bono
                    df_con_tir = df_resultados[df_resultados['TIR (%)'].notna()]
                    if not df_con_tir.empty:
                        fig_tir = px.bar(
                            df_con_tir,
                            x='Símbolo',
                            y='TIR (%)',
                            title=f'TIR por Bono - Categoría: {categoria_seleccionada}',
                            color='TIR (%)',
                            color_continuous_scale='RdYlGn'
                        )
                        st.plotly_chart(fig_tir, use_container_width=True)
                        
                        # Estadísticas
                        st.write("#### Estadísticas:")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("TIR Promedio", f"{df_con_tir['TIR (%)'].mean():.2f}%")
                        with col2:
                            st.metric("TIR Máxima", f"{df_con_tir['TIR (%)'].max():.2f}%")
                        with col3:
                            st.metric("TIR Mínima", f"{df_con_tir['TIR (%)'].min():.2f}%")
                else:
                    st.warning("No se pudieron obtener resultados para esta categoría")
        else:
            st.warning(f"No hay bonos disponibles para la categoría: {categoria_seleccionada}")

# Selección de bonos basada en tickers extraídos y mapeados a datos técnicos
if categoria_seleccionada:
    bonos_categoria = obtener_bonos_por_categoria(categoria_seleccionada)
    tickers_extraidos = bonos_categoria
    asociacion_ticker_dato = mapear_tickers_a_datos_tecnicos(tickers_extraidos, INSTRUMENTOS_FINANCIEROS)
    bonos_disponibles = list(asociacion_ticker_dato.keys())
    default_bonos = bonos_disponibles[:3] if len(bonos_disponibles) >= 3 else bonos_disponibles
else:
    bonos_disponibles = list(INSTRUMENTOS_FINANCIEROS.keys())
    default_bonos = ["AE38D", "AE35D", "BONCER2025"]

bonos_seleccionados = st.multiselect(
    "Seleccione bonos para analizar:",
    bonos_disponibles,
    default=default_bonos,
    key="bonos_seleccionados"
)

