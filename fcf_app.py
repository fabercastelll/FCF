import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Calculadora de Flujo de Caja", page_icon="💰", layout="wide")

# --- Funciones Utilitarias ---
def formatear_pyg(valor):
    if isinstance(valor, (int, float)):
        return f'Gs. {int(valor):,}'.replace(',', '.')
    return valor

def calcular_operaciones(inversion, costo_op):
    return max(1, inversion // costo_op) if costo_op > 0 else 0

def inicializar_estado():
    if 'reinversiones_compra' not in st.session_state:
        st.session_state.reinversiones_compra = []
    if 'reinversiones_colocacion' not in st.session_state:
        st.session_state.reinversiones_colocacion = []

def agregar_reinversion(tipo, valores):
    nueva_reinversion = dict(valores)
    if tipo == "Compra":
        st.session_state.reinversiones_compra.append(nueva_reinversion)
    else:
        st.session_state.reinversiones_colocacion.append(nueva_reinversion)

def resetear(tipo=None):
    if tipo == "Compra":
        st.session_state.reinversiones_compra = []
    elif tipo == "Colocación":
        st.session_state.reinversiones_colocacion = []
    else:
        st.session_state.reinversiones_compra = []
        st.session_state.reinversiones_colocacion = []

def generar_flujo(inv_inicial, costo_inicial, cuotas_inicial, importe_inicial, no_cobro_inicial, ops_inicial, reinversiones, meses=60):
    flujo_caja = pd.DataFrame(0, index=range(meses), columns=["Ingresos", "Reinversión", "Total Cobrado", "Saldo Acumulado", "Total Disponible", "No Cobro", "Operaciones Abiertas"])
    flujo_caja.loc[0, "Saldo Acumulado"] = -inv_inicial
    
    for i in range(min(cuotas_inicial, meses - 1)):
        mes = i + 1
        ingreso_real = ops_inicial * (importe_inicial * (1 - no_cobro_inicial / 100))
        flujo_caja.loc[mes, ["Ingresos", "No Cobro", "Operaciones Abiertas"]] += [ingreso_real, ops_inicial * (importe_inicial * (no_cobro_inicial / 100)), ops_inicial]
    
    for reinv in reinversiones:
        mes_inv = min(reinv["mes"], meses - 1)
        flujo_caja.loc[mes_inv, "Reinversión"] += reinv["inversion"]
        for i in range(min(reinv["cuotas"], meses - reinv["mes"])):
            mes = reinv["mes"] + i
            ingreso_real = reinv["ops"] * (reinv["importe"] * (1 - reinv["no_cobro"] / 100))
            flujo_caja.loc[mes, ["Ingresos", "No Cobro", "Operaciones Abiertas"]] += [ingreso_real, reinv["ops"] * (reinv["importe"] * (reinv["no_cobro"] / 100)), reinv["ops"]]
    
    flujo_caja["Total Cobrado"] = flujo_caja["Ingresos"].cumsum()
    flujo_caja["Saldo Acumulado"] = flujo_caja["Saldo Acumulado"].iloc[0] + flujo_caja["Ingresos"].cumsum() - flujo_caja["Reinversión"].cumsum()
    flujo_caja["Total Disponible"] = flujo_caja["Ingresos"].cumsum() - flujo_caja["Reinversión"].cumsum()
    
    return flujo_caja.applymap(formatear_pyg)

# --- UI ---
inicializar_estado()
st.title("Calculadora de Flujo de Caja")
st.markdown("---")

# Secciones de inversión y reinversión
col_inicial, col_compra, col_colocacion = st.columns(3)

with col_inicial:
    st.header("Inversión Inicial")
    inv_inicial = st.number_input("Inversión:", min_value=0, value=300000000, step=1000000)
    costo_inicial = st.number_input("Costo Op:", min_value=1, value=6000000, step=100000)
    ops_inicial = calcular_operaciones(inv_inicial, costo_inicial)
    cuotas_inicial = st.number_input("Cuotas:", min_value=1, value=14, step=1)
    importe_inicial = st.number_input("Importe:", min_value=0, value=1500000, step=100000)
    no_cobro_inicial = st.slider("% No Cobro:", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    st.metric("Operaciones:", ops_inicial)
    ejecutar = st.button("Ejecutar Inversión Inicial")

# Función para crear UI de reinversión
def crear_reinversion_ui(tipo, session_key):
    with st.container():
        st.header(f"Reinversión {tipo}")
        valores = {
            "mes": st.number_input("Mes:", min_value=1, value=1, step=1, key=f"mes_{session_key}"),
            "inversion": st.number_input("Inversión:", min_value=0, value=6000000, step=1000000, key=f"inversion_{session_key}"),
            "cuotas": st.number_input("Cuotas:", min_value=1, value=14, step=1, key=f"cuotas_{session_key}"),
            "importe": st.number_input("Importe:", min_value=0, value=1500000, step=100000, key=f"importe_{session_key}"),
            "no_cobro": st.slider("% No Cobro:", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key=f"no_cobro_{session_key}"),
            "ops": calcular_operaciones(st.session_state[f"inversion_{session_key}"], costo_inicial)
        }
        if st.button(f"Agregar {tipo}"):
            agregar_reinversion(tipo, valores)

with col_compra:
    crear_reinversion_ui("Compra", "compra")

with col_colocacion:
    crear_reinversion_ui("Colocación", "colocacion")

st.markdown("---")

if ejecutar or st.session_state.reinversiones_compra or st.session_state.reinversiones_colocacion:
    st.header("Flujo de Caja")
    flujo_caja = generar_flujo(inv_inicial, costo_inicial, cuotas_inicial, importe_inicial, no_cobro_inicial, ops_inicial, st.session_state.reinversiones_compra + st.session_state.reinversiones_colocacion)
    st.dataframe(flujo_caja, use_container_width=True)
