import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Flujo de Caja",
    page_icon="💰",
    layout="wide"
)

# Función para formatear números en PYG sin decimales
def formatear_pyg(valor):
    if isinstance(valor, (int, float)):
        return f'Gs. {int(valor):,}'.replace(',', '.')
    return valor

def calcular_operaciones(inversion, costo_op):
    """Calcular número de operaciones basadas en inversión y costo"""
    try:
        if costo_op > 0:
            return max(1, inversion // costo_op)
        return 0
    except:
        return 0

# Crear listas para almacenar reinversiones (mantener estado en st.session_state)
if 'reinversiones_compra' not in st.session_state:
    st.session_state.reinversiones_compra = []
    
if 'reinversiones_colocacion' not in st.session_state:
    st.session_state.reinversiones_colocacion = []

# Función para generar flujo de caja
def generar_flujo(
    inv_inicial, 
    costo_inicial, 
    cuotas_inicial, 
    importe_inicial, 
    cuota_final_inicial,
    no_cobro_inicial, 
    ops_inicial, 
    meses_demora_inicial,
    reinversiones_compra,
    reinversiones_colocacion,
    meses=60
):
    """Generar el flujo de caja basado en parámetros de entrada"""
    # Crear dataframe para el flujo de caja
    flujo_caja = pd.DataFrame(
        np.zeros((meses, 7)),
        columns=["Ingresos", "Reinversión", "Total Cobrado", "Saldo Acumulado", "Total Disponible", "No Cobro", "Operaciones Abiertas"]
    )
    
    # Aplicar inversión inicial
    flujo_caja.loc[0, "Saldo Acumulado"] = -inv_inicial
    
    # Procesar ingresos de inversión inicial con retraso
    for i in range(min(cuotas_inicial, meses - 1)):
        mes = i + 1 + meses_demora_inicial
        if mes < meses:
            ingreso_real = ops_inicial * (importe_inicial * (1 - no_cobro_inicial / 100))
            flujo_caja.loc[mes, "Ingresos"] += ingreso_real
            flujo_caja.loc[mes, "No Cobro"] += ops_inicial * (importe_inicial * (no_cobro_inicial / 100))
            flujo_caja.loc[mes, "Operaciones Abiertas"] += ops_inicial
    
    # Procesar reinversiones
    for reinv_list in [reinversiones_compra, reinversiones_colocacion]:
        for reinv in reinv_list:
            mes_inversion = min(reinv["mes"], meses - 1)
            flujo_caja.loc[mes_inversion, "Reinversión"] += reinv["inversion"]
            
            for i in range(min(reinv["cuotas"], meses - reinv["mes"] - reinv["meses_demora"])):
                mes = reinv["mes"] + i + reinv["meses_demora"]
                if mes < meses:
                    ingreso_real = reinv["ops"] * (reinv["importe"] * (1 - reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Ingresos"] += ingreso_real
                    flujo_caja.loc[mes, "No Cobro"] += reinv["ops"] * (reinv["importe"] * (reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Operaciones Abiertas"] += reinv["ops"]
    
    # Calcular totales acumulados
    flujo_caja["Total Cobrado"] = flujo_caja["Ingresos"].cumsum()
    flujo_caja["Saldo Acumulado"] = (
        flujo_caja.loc[0, "Saldo Acumulado"] + 
        flujo_caja["Ingresos"].cumsum() - 
        flujo_caja["Reinversión"].cumsum()
    )
    flujo_caja["Total Disponible"] = flujo_caja["Ingresos"].cumsum() - flujo_caja["Reinversión"].cumsum()
    
    return flujo_caja

# Función para agregar reinversión
def agregar_reinversion(tipo_reinversion, mes, inversion, cuotas, importe, cuota_final, no_cobro, ops, meses_demora):
    nueva_reinversion = {
        "mes": mes,
        "inversion": inversion,
        "cuotas": cuotas,
        "importe": importe,
        "cuota_final": cuota_final,
        "no_cobro": no_cobro,
        "ops": ops,
        "meses_demora": meses_demora
    }
    
    if tipo_reinversion == "Compra":
        st.session_state.reinversiones_compra.append(nueva_reinversion)
    else:
        st.session_state.reinversiones_colocacion.append(nueva_reinversion)
    
    return True

# Función para resetear datos
def reset_all():
    st.session_state.reinversiones_compra = []
    st.session_state.reinversiones_colocacion = []
    return True

def reset_reinversion(tipo):
    if tipo == "Compra":
        st.session_state.reinversiones_compra = []
    else:
        st.session_state.reinversiones_colocacion = []
    return True

# Título principal
st.title("Calculadora de Flujo de Caja")
st.write("Herramienta para simular flujos de caja con inversiones iniciales y reinversiones")

# Crear tres columnas para las secciones
col_inicial, col_compra, col_colocacion = st.columns(3)

# ---- Sección de Inversión Inicial ----
with col_inicial:
    st.header("Inversión Inicial")
    
    inv_inicial = st.number_input(
        "Inversión:", 
        min_value=0, 
        value=300000000, 
        step=1000000,
        key="inv_inicial"
    )
    
    costo_inicial = st.number_input(
        "Costo Operativo:", 
        min_value=1, 
        value=6000000, 
        step=100000,
        key="costo_inicial"
    )
    
    # Calcular operaciones automáticamente
    ops_inicial = calcular_operaciones(inv_inicial, costo_inicial)
    
    cuotas_inicial = st.number_input(
        "Cuotas:", 
        min_value=1, 
        value=14, 
        step=1,
        key="cuotas_inicial"
    )
    
    importe_inicial = st.number_input(
        "Importe:", 
        min_value=0, 
        value=1500000, 
        step=100000,
        key="importe_inicial"
    )
    
    cuota_final_inicial = st.number_input(
        "Cuota Final:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="cuota_final_inicial"
    )
    
    no_cobro_inicial = st.slider(
        "% No Cobro:", 
        min_value=0.0, 
        max_value=100.0, 
        value=0.0, 
        step=0.5,
        key="no_cobro_inicial"
    )
    
    # Mostrar operaciones calculadas
    st.metric("Operaciones:", ops_inicial)
    
    meses_demora_inicial = st.number_input(
        "Meses Demora:", 
        min_value=0, 
        value=0, 
        step=1,
        key="meses_demora_inicial"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        ejecutar_inversion = st.button("Ejecutar Inversión Inicial", type="primary")
    with col2:
        reset_inicial = st.button("Reset Inicial", type="secondary")
        if reset_inicial:
            reset_all()
            st.success("Inversión inicial y reinversiones reiniciados")
            st.experimental_rerun()

# ---- Sección Reinversión Compra ----
with col_compra:
    st.header("Reinversión Compra")
    
    mes_compra = st.number_input(
        "Mes:", 
        min_value=1, 
        value=1, 
        step=1,
        key="mes_compra"
    )
    
    inversion_compra = st.number_input(
        "Inversión:", 
        min_value=0, 
        value=6000000, 
        step=1000000,
        key="inversion_compra"
    )
    
    costo_op_compra = st.number_input(
        "Costo Op:", 
        min_value=1, 
        value=6000000, 
        step=100000,
        key="costo_op_compra"
    )
    
    # Cálculo automático de operaciones
    ops_compra = calcular_operaciones(inversion_compra, costo_op_compra)
    
    cuotas_compra = st.number_input(
        "Cuotas:", 
        min_value=1, 
        value=14, 
        step=1,
        key="cuotas_compra"
    )
    
    importe_compra = st.number_input(
        "Importe:", 
        min_value=0, 
        value=1500000, 
        step=100000,
        key="importe_compra"
    )
    
    cuota_final_compra = st.number_input(
        "Cuota Final:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="cuota_final_compra"
    )
    
    no_cobro_compra = st.slider(
        "% No Cobro:", 
        min_value=0.0, 
        max_value=100.0, 
        value=0.0, 
        step=0.5,
        key="no_cobro_compra"
    )
    
    # Mostrar operaciones calculadas
    st.metric("Operaciones:", ops_compra)
    
    meses_demora_compra = st.number_input(
        "Meses Demora:", 
        min_value=0, 
        value=0, 
        step=1,
        key="meses_demora_compra"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        agregar_compra = st.button("Agregar Compra", type="primary")
        if agregar_compra:
            if agregar_reinversion(
                "Compra", 
                mes_compra, 
                inversion_compra, 
                cuotas_compra, 
                importe_compra,
                cuota_final_compra,
                no_cobro_compra,
                ops_compra,
                meses_demora_compra
            ):
                st.success(f"Reinversión Compra agregada en mes {mes_compra}")
    
    with col2:
        reset_compra = st.button("Reset Compra", type="secondary")
        if reset_compra:
            reset_reinversion("Compra")
            st.success("Reinversiones Compra reiniciadas")

# ---- Sección Reinversión Colocación ----
with col_colocacion:
    st.header("Reinversión Colocación")
    
    mes_colocacion = st.number_input(
        "Mes:", 
        min_value=1, 
        value=1, 
        step=1,
        key="mes_colocacion"
    )
    
    inversion_colocacion = st.number_input(
        "Inversión:", 
        min_value=0, 
        value=6000000, 
        step=1000000,
        key="inversion_colocacion"
    )
    
    costo_op_colocacion = st.number_input(
        "Costo Op:", 
        min_value=1, 
        value=6000000, 
        step=100000,
        key="costo_op_colocacion"
    )
    
    # Cálculo automático de operaciones
    ops_colocacion = calcular_operaciones(inversion_colocacion, costo_op_colocacion)
    
    cuotas_colocacion = st.number_input(
        "Cuotas:", 
        min_value=1, 
        value=14, 
        step=1,
        key="cuotas_colocacion"
    )
    
    importe_colocacion = st.number_input(
        "Importe:", 
        min_value=0, 
        value=1500000, 
        step=100000,
        key="importe_colocacion"
    )
    
    cuota_final_colocacion = st.number_input(
        "Cuota Final:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="cuota_final_colocacion"
    )
    
    no_cobro_colocacion = st.slider(
        "% No Cobro:", 
        min_value=0.0, 
        max_value=100.0, 
        value=0.0, 
        step=0.5,
        key="no_cobro_colocacion"
    )
    
    # Mostrar operaciones calculadas
    st.metric("Operaciones:", ops_colocacion)
    
    meses_demora_colocacion = st.number_input(
        "Meses Demora:", 
        min_value=0, 
        value=0, 
        step=1,
        key="meses_demora_colocacion"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        agregar_colocacion = st.button("Agregar Colocación", type="primary")
        if agregar_colocacion:
            if agregar_reinversion(
                "Colocacion", 
                mes_colocacion, 
                inversion_colocacion, 
                cuotas_colocacion, 
                importe_colocacion,
                cuota_final_colocacion,
                no_cobro_colocacion,
                ops_colocacion,
                meses_demora_colocacion
            ):
                st.success(f"Reinversión Colocación agregada en mes {mes_colocacion}")
    
    with col2:
        reset_colocacion = st.button("Reset Colocación", type="secondary")
        if reset_colocacion:
            reset_reinversion("Colocacion")
            st.success("Reinversiones Colocación reiniciadas")

# Botón de Reset General
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    reset_todo = st.button("Reset Todo", type="secondary", key="reset_todo")
    if reset_todo:
        reset_all()
        st.success("Todas las reinversiones han sido reiniciadas")
        st.experimental_rerun()

# Generar y mostrar el flujo de caja
if ejecutar_inversion or agregar_compra or agregar_colocacion or st.session_state.reinversiones_compra or st.session_state.reinversiones_colocacion:
    st.header("Flujo de Caja")
    
    # Resumen de reinversiones si hay alguna
    if st.session_state.reinversiones_compra or st.session_state.reinversiones_colocacion:
        st.subheader("Resumen de Reinversiones")
        resumen_col1, resumen_col2 = st.columns(2)
        
        with resumen_col1:
            st.write(f"Reinversiones Compra: {len(st.session_state.reinversiones_compra)}")
        
        with resumen_col2:
            st.write(f"Reinversiones Colocación: {len(st.session_state.reinversiones_colocacion)}")
    
    # Generar flujo de caja
    flujo_caja = generar_flujo(
        inv_inicial=inv_inicial,
        costo_inicial=costo_inicial,
        cuotas_inicial=cuotas_inicial,
        importe_inicial=importe_inicial,
        cuota_final_inicial=cuota_final_inicial,
        no_cobro_inicial=no_cobro_inicial,
        ops_inicial=ops_inicial,
        meses_demora_inicial=meses_demora_inicial,
        reinversiones_compra=st.session_state.reinversiones_compra,
        reinversiones_colocacion=st.session_state.reinversiones_colocacion
    )
    
    # Formatear valores
    for col in ["Ingresos", "Reinversión", "Total Cobrado", "Saldo Acumulado", "Total Disponible", "No Cobro"]:
        flujo_caja[col] = flujo_caja[col].map(formatear_pyg)
    
    # Mostrar tabla de flujo de caja
    st.dataframe(flujo_caja, use_container_width=True)
    
    # Agregar opción para descargar como CSV
    csv = flujo_caja.to_csv(index=True)
    st.download_button(
        label="Descargar como CSV",
        data=csv,
        file_name="flujo_de_caja.csv",
        mime="text/csv",
    )
