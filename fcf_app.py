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
    meses_sin_cobros_inicial,
    cuotas_regulacion_inicial,
    importe_regulacion_inicial,
    pct_distribucion_inicial,
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
    
    # Procesar cuotas de regulación inicial
    # Calcular mes de inicio para las cuotas de regulación (después de las cuotas iniciales + meses sin cobros)
    mes_inicio_regulacion = meses_demora_inicial + cuotas_inicial + meses_sin_cobros_inicial
    
    for i in range(min(cuotas_regulacion_inicial, meses - mes_inicio_regulacion)):
        mes = mes_inicio_regulacion + i
        if mes < meses:
            # Aplicar el porcentaje de distribución al importe de la regulación
            importe_ajustado = importe_regulacion_inicial * (pct_distribucion_inicial / 100)
            ingreso_real = ops_inicial * (importe_ajustado * (1 - no_cobro_inicial / 100))
            flujo_caja.loc[mes, "Ingresos"] += ingreso_real
            flujo_caja.loc[mes, "No Cobro"] += ops_inicial * (importe_ajustado * (no_cobro_inicial / 100))
            # No incrementamos operaciones abiertas aquí porque son las mismas operaciones iniciales
    
    # Procesar reinversiones
    for reinv_list in [reinversiones_compra, reinversiones_colocacion]:
        for reinv in reinv_list:
            mes_inversion = min(reinv["mes"], meses - 1)
            flujo_caja.loc[mes_inversion, "Reinversión"] += reinv["inversion"]
            
            # Procesar ingresos normales de las reinversiones
            for i in range(min(reinv["cuotas"], meses - reinv["mes"] - reinv["meses_demora"])):
                mes = reinv["mes"] + i + reinv["meses_demora"]
                if mes < meses:
                    ingreso_real = reinv["ops"] * (reinv["importe"] * (1 - reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Ingresos"] += ingreso_real
                    flujo_caja.loc[mes, "No Cobro"] += reinv["ops"] * (reinv["importe"] * (reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Operaciones Abiertas"] += reinv["ops"]
            
            # Procesar cuotas de regulación de las reinversiones
            mes_inicio_regulacion_reinv = reinv["mes"] + reinv["meses_demora"] + reinv["cuotas"] + reinv["meses_sin_cobros"]
            
            for i in range(min(reinv["cuotas_regulacion"], meses - mes_inicio_regulacion_reinv)):
                mes = mes_inicio_regulacion_reinv + i
                if mes < meses:
                    # Aplicar el porcentaje de distribución al importe de la regulación
                    importe_ajustado = reinv["importe_regulacion"] * (reinv["pct_distribucion"] / 100)
                    ingreso_real = reinv["ops"] * (importe_ajustado * (1 - reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Ingresos"] += ingreso_real
                    flujo_caja.loc[mes, "No Cobro"] += reinv["ops"] * (importe_ajustado * (reinv["no_cobro"] / 100))
                    # No incrementamos operaciones abiertas aquí porque son las mismas operaciones de la reinversión
    
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
def agregar_reinversion(tipo_reinversion, mes, inversion, cuotas, importe, 
                        meses_sin_cobros, cuotas_regulacion, importe_regulacion, 
                        pct_distribucion, no_cobro, ops, meses_demora):
    nueva_reinversion = {
        "mes": mes,
        "inversion": inversion,
        "cuotas": cuotas,
        "importe": importe,
        "meses_sin_cobros": meses_sin_cobros,
        "cuotas_regulacion": cuotas_regulacion,
        "importe_regulacion": importe_regulacion,
        "pct_distribucion": pct_distribucion,
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

# Título principal y botón de Reset Todo en la parte superior
header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.title("Calculadora de Flujo de Caja")
    st.write("Herramienta para simular flujos de caja con inversiones iniciales y reinversiones")

with header_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Espacio para alinear con el título
    reset_todo_superior = st.button("🔄 RESET TODO", type="primary", key="reset_todo_superior", 
                          use_container_width=True, 
                          help="Reinicia todas las inversiones y configuraciones")
    if reset_todo_superior:
        reset_all()
        st.success("Todas las reinversiones han sido reiniciadas")
        st.experimental_rerun()

# Línea divisoria debajo del título
st.markdown("---")

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
    
    # Nuevos campos para reemplazar Cuota Final
    st.markdown("---")  # Línea divisoria
    st.subheader("Regulación")
    
    meses_sin_cobros_inicial = st.number_input(
        "Meses sin cobros:", 
        min_value=0, 
        value=6, 
        step=1,
        key="meses_sin_cobros_inicial"
    )
    
    cuotas_regulacion_inicial = st.number_input(
        "Cuotas Regulación:", 
        min_value=0, 
        value=5, 
        step=1,
        key="cuotas_regulacion_inicial"
    )
    
    importe_regulacion_inicial = st.number_input(
        "Importe Cuota Regulación:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="importe_regulacion_inicial"
    )
    
    # Usar radio buttons para el % de Distribución
    st.write("% Distribución Regulación:")
    pct_distribucion_inicial = st.radio(
        "",
        options=[20, 40, 60, 80],
        index=1,  # Predeterminado 40% (índice 1)
        horizontal=True,
        key="pct_distribucion_inicial"
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
    
    # Nuevos campos para reemplazar Cuota Final en Compra
    st.markdown("---")  # Línea divisoria
    st.subheader("Regulación")
    
    meses_sin_cobros_compra = st.number_input(
        "Meses sin cobros:", 
        min_value=0, 
        value=6, 
        step=1,
        key="meses_sin_cobros_compra"
    )
    
    cuotas_regulacion_compra = st.number_input(
        "Cuotas Regulación:", 
        min_value=0, 
        value=5, 
        step=1,
        key="cuotas_regulacion_compra"
    )
    
    importe_regulacion_compra = st.number_input(
        "Importe Cuota Regulación:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="importe_regulacion_compra"
    )
    
    # Usar radio buttons para el % de Distribución
    st.write("% Distribución Regulación:")
    pct_distribucion_compra = st.radio(
        "",
        options=[20, 40, 60, 80],
        index=1,  # Predeterminado 40% (índice 1)
        horizontal=True,
        key="pct_distribucion_compra"
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
                meses_sin_cobros_compra,
                cuotas_regulacion_compra,
                importe_regulacion_compra,
                pct_distribucion_compra,
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
    
    # Nuevos campos para reemplazar Cuota Final en Colocación
    st.markdown("---")  # Línea divisoria
    st.subheader("Regulación")
    
    meses_sin_cobros_colocacion = st.number_input(
        "Meses sin cobros:", 
        min_value=0, 
        value=6, 
        step=1,
        key="meses_sin_cobros_colocacion"
    )
    
    cuotas_regulacion_colocacion = st.number_input(
        "Cuotas Regulación:", 
        min_value=0, 
        value=5, 
        step=1,
        key="cuotas_regulacion_colocacion"
    )
    
    importe_regulacion_colocacion = st.number_input(
        "Importe Cuota Regulación:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="importe_regulacion_colocacion"
    )
    
    # Usar radio buttons para el % de Distribución
    st.write("% Distribución Regulación:")
    pct_distribucion_colocacion = st.radio(
        "",
        options=[20, 40, 60, 80],
        index=1,  # Predeterminado 40% (índice 1)
        horizontal=True,
        key="pct_distribucion_colocacion"
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
                meses_sin_cobros_colocacion,
                cuotas_regulacion_colocacion,
                importe_regulacion_colocacion,
                pct_distribucion_colocacion,
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

# Ya no es necesario el botón de Reset Todo aquí, se movió a la parte superior de la página

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
        meses_sin_cobros_inicial=meses_sin_cobros_inicial,
        cuotas_regulacion_inicial=cuotas_regulacion_inicial,
        importe_regulacion_inicial=importe_regulacion_inicial,
        pct_distribucion_inicial=pct_distribucion_inicial,
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
