import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Flujo de Caja",
    page_icon="💰",
    layout="wide"
)

# Agregar CSS personalizado para las líneas divisorias y alineación
st.markdown("""
<style>
    /* Ajustar altura mínima de las secciones principales para alinear divisores */
    .seccion-principal {
        min-height: 380px;
        position: relative;
        padding-bottom: 20px;
    }

    /* Posicionamiento absoluto para las líneas divisorias */
    .linea-divisoria {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        border-top: 2px solid #e6e6e6;
        margin-top: 20px;
        margin-bottom: 20px;
        width: 100%;
    }
    
    /* Estilo para las secciones de cálculo */
    .stSelectbox, .stNumberInput, .stSlider {
        margin-bottom: 15px;
    }
    
    /* Destacar los botones principales */
    .stButton button[data-baseweb="button"] {
        font-weight: bold;
    }
    
    /* Hacer que los botones tengan el mismo tamaño */
    .boton-accion button {
        width: 100% !important;
        margin-top: 10px;
        height: 46px !important;
    }
    
    /* Mejorar la legibilidad de la tabla */
    .dataframe {
        font-size: 14px !important;
    }
    
    /* Destacar la métrica de operaciones */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #0068c9 !important;
    }
    
    /* Mejorar visibilidad de los títulos de sección */
    h3 {
        margin-top: 10px !important;
        color: #0068c9 !important;
    }

    /* Ajuste para los radiobuttons */
    .radio-container {
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* Establecer lugar fijo para Meses Hasta Primer Cobro */
    .campo-meses-primer-cobro {
        margin-top: 10px;
        margin-bottom: 30px;
    }
    
    /* Botón de reinversión automática (amarillo) */
    .boton-reinversion-auto button {
        background-color: #FFC107 !important;
        border-color: #FFC107 !important;
        color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)

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
    pago_mensual,
    meses_pago,
    meses_total
):
    """Generar el flujo de caja basado en parámetros de entrada"""
    # Crear dataframe para el flujo de caja
    flujo_caja = pd.DataFrame(
        np.zeros((meses_total, 10)),
        columns=["Ingresos", "Reinversión", "Pago Mensual", "Total Cobrado", "Saldo Acumulado", "Total Disponible", "No Cobro", "Operaciones Abiertas", "Reinversiones Automáticas Mes", "Reinversiones Automáticas Total"]
    )
    
    # Aplicar inversión inicial
    flujo_caja.loc[0, "Saldo Acumulado"] = -inv_inicial
    
    # Aplicar pago mensual solo durante los meses especificados
    for mes in range(1, min(meses_pago + 1, meses_total)):
        flujo_caja.loc[mes, "Pago Mensual"] = pago_mensual
    
    # Procesar ingresos de inversión inicial con retraso
    for i in range(min(cuotas_inicial, meses_total - 1)):
        mes = i + 1 + meses_demora_inicial
        if mes < meses_total:
            ingreso_real = ops_inicial * (importe_inicial * (1 - no_cobro_inicial / 100))
            flujo_caja.loc[mes, "Ingresos"] += ingreso_real
            flujo_caja.loc[mes, "No Cobro"] += ops_inicial * (importe_inicial * (no_cobro_inicial / 100))
            flujo_caja.loc[mes, "Operaciones Abiertas"] += ops_inicial
    
    # Procesar cuotas de regulación inicial
    # Calcular mes de inicio para las cuotas de regulación (después de las cuotas iniciales + meses sin cobros)
    mes_inicio_regulacion = meses_demora_inicial + cuotas_inicial + meses_sin_cobros_inicial
    
    for i in range(min(cuotas_regulacion_inicial, meses_total - mes_inicio_regulacion)):
        mes = mes_inicio_regulacion + i
        if mes < meses_total:
            # Aplicar el porcentaje de distribución al importe de la regulación
            importe_ajustado = importe_regulacion_inicial * (pct_distribucion_inicial / 100)
            ingreso_real = ops_inicial * (importe_ajustado * (1 - no_cobro_inicial / 100))
            flujo_caja.loc[mes, "Ingresos"] += ingreso_real
            flujo_caja.loc[mes, "No Cobro"] += ops_inicial * (importe_ajustado * (no_cobro_inicial / 100))
            # No incrementamos operaciones abiertas aquí porque son las mismas operaciones iniciales
    
    # Procesar reinversiones
    for reinv_list in [reinversiones_compra, reinversiones_colocacion]:
        for reinv in reinv_list:
            mes_inversion = min(reinv["mes"], meses_total - 1)
            flujo_caja.loc[mes_inversion, "Reinversión"] += reinv["inversion"]
            
            # Incrementar contador de reinversiones automáticas si corresponde
            if reinv.get("automatica", False) and reinv_list == reinversiones_colocacion:
                flujo_caja.loc[mes_inversion, "Reinversiones Automáticas Mes"] += 1
            
            # Procesar ingresos normales de las reinversiones
            for i in range(min(reinv["cuotas"], meses_total - reinv["mes"] - reinv["meses_demora"])):
                mes = reinv["mes"] + i + reinv["meses_demora"]
                if mes < meses_total:
                    ingreso_real = reinv["ops"] * (reinv["importe"] * (1 - reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Ingresos"] += ingreso_real
                    flujo_caja.loc[mes, "No Cobro"] += reinv["ops"] * (reinv["importe"] * (reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Operaciones Abiertas"] += reinv["ops"]
            
            # Procesar cuotas de regulación de las reinversiones
            mes_inicio_regulacion_reinv = reinv["mes"] + reinv["meses_demora"] + reinv["cuotas"] + reinv["meses_sin_cobros"]
            
            for i in range(min(reinv["cuotas_regulacion"], meses_total - mes_inicio_regulacion_reinv)):
                mes = mes_inicio_regulacion_reinv + i
                if mes < meses_total:
                    # Aplicar el porcentaje de distribución al importe de la regulación
                    importe_ajustado = reinv["importe_regulacion"] * (reinv["pct_distribucion"] / 100)
                    ingreso_real = reinv["ops"] * (importe_ajustado * (1 - reinv["no_cobro"] / 100))
                    flujo_caja.loc[mes, "Ingresos"] += ingreso_real
                    flujo_caja.loc[mes, "No Cobro"] += reinv["ops"] * (importe_ajustado * (reinv["no_cobro"] / 100))
                    # No incrementamos operaciones abiertas aquí porque son las mismas operaciones de la reinversión
    
    # Calcular totales acumulados
    flujo_caja["Total Cobrado"] = flujo_caja["Ingresos"].cumsum()
    
    # Calcular Saldo Acumulado considerando pago mensual
    flujo_caja["Saldo Acumulado"] = (
        flujo_caja.loc[0, "Saldo Acumulado"] + 
        flujo_caja["Ingresos"].cumsum() - 
        flujo_caja["Reinversión"].cumsum() -
        flujo_caja["Pago Mensual"].cumsum()
    )
    
    flujo_caja["Total Disponible"] = flujo_caja["Ingresos"].cumsum() - flujo_caja["Reinversión"].cumsum() - flujo_caja["Pago Mensual"].cumsum()
    
    # Calcular totales acumulados de reinversiones automáticas
    reinv_auto_acumuladas = 0
    for i in range(meses_total):
        reinv_auto_acumuladas += flujo_caja.loc[i, "Reinversiones Automáticas Mes"]
        flujo_caja.loc[i, "Reinversiones Automáticas Total"] = reinv_auto_acumuladas
    
    return flujo_caja

# Función para agregar reinversión
def agregar_reinversion(tipo_reinversion, mes, inversion, cuotas, importe, 
                        meses_sin_cobros, cuotas_regulacion, importe_regulacion, 
                        pct_distribucion, no_cobro, ops, meses_demora, automatica=False):
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
        "meses_demora": meses_demora,
        "automatica": automatica
    }
    
    if tipo_reinversion == "Compra":
        st.session_state.reinversiones_compra.append(nueva_reinversion)
    else:
        st.session_state.reinversiones_colocacion.append(nueva_reinversion)
    
    return True

# Función para ejecutar reinversiones automáticas
def ejecutar_reinversion_automatica(
    inversion_colocacion, 
    costo_op_colocacion, 
    cuotas_colocacion, 
    importe_colocacion, 
    meses_sin_cobros_colocacion, 
    cuotas_regulacion_colocacion, 
    importe_regulacion_colocacion, 
    pct_distribucion_colocacion, 
    no_cobro_colocacion, 
    meses_demora_colocacion,
    meses_pago,
    meses_total
):
    # Generar un flujo de caja temporal con las reinversiones actuales
    flujo_temp = generar_flujo(
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
        reinversiones_colocacion=st.session_state.reinversiones_colocacion,
        pago_mensual=pago_mensual,
        meses_pago=meses_pago,
        meses_total=meses_total
    )
    
    # Costo por reinversión y operaciones que se generan
    ops_por_reinversion = calcular_operaciones(inversion_colocacion, costo_op_colocacion)
    
    # Contador de reinversiones automáticas
    reinversiones_agregadas = 0
    
    # Recorrer todos los meses para ver dónde hay fondos disponibles
    for mes in range(1, meses_total):  # Empezar desde el mes 1
        # Convertir el valor a número
        disponible = flujo_temp.loc[mes, "Total Disponible"]
        if isinstance(disponible, str):
            disponible = float(disponible.replace('Gs. ', '').replace('.', ''))
        
        # Verificar si hay suficiente para al menos una reinversión
        while disponible >= inversion_colocacion:
            # Agregar una reinversión automática para este mes
            agregar_reinversion(
                "Colocacion",
                mes,  # Mes actual
                inversion_colocacion,
                cuotas_colocacion,
                importe_colocacion,
                meses_sin_cobros_colocacion,
                cuotas_regulacion_colocacion,
                importe_regulacion_colocacion,
                pct_distribucion_colocacion,
                no_cobro_colocacion,
                ops_por_reinversion,
                meses_demora_colocacion,
                automatica=True  # Marcar como automática
            )
            
            reinversiones_agregadas += 1
            
            # Actualizar el disponible restando la inversión
            disponible -= inversion_colocacion
            
            # Regenerar el flujo temporal para la próxima iteración
            flujo_temp = generar_flujo(
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
                reinversiones_colocacion=st.session_state.reinversiones_colocacion,
                pago_mensual=pago_mensual,
                meses_pago=meses_pago,
                meses_total=meses_total
            )
            
            # Actualizar el disponible después de recalcular el flujo
            disponible = flujo_temp.loc[mes, "Total Disponible"]
            if isinstance(disponible, str):
                disponible = float(disponible.replace('Gs. ', '').replace('.', ''))
    
    return reinversiones_agregadas

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
    # Agregar campo para pago mensual
    pago_mensual = st.number_input(
        "Pago Mensual:", 
        min_value=0, 
        value=5000000, 
        step=100000,
        key="pago_mensual",
        help="Cantidad mensual que se deducirá del flujo de caja"
    )
    
    # Nuevos campos para duración de pagos y proyección total
    meses_pago = st.number_input(
        "Meses de Pago:", 
        min_value=1, 
        max_value=360,
        value=60, 
        step=12,
        key="meses_pago",
        help="Número de meses en los que se aplicará el pago mensual"
    )
    
    meses_total = st.number_input(
        "Meses a Proyectar:", 
        min_value=12, 
        max_value=360,
        value=100, 
        step=12,
        key="meses_total",
        help="Número total de meses a incluir en el flujo de caja"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)  # Espacio para alinear con el título
    st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
    reset_todo_superior = st.button("🔄 RESET TODO", type="primary", key="reset_todo_superior", 
                          use_container_width=True, 
                          help="Reinicia todas las inversiones y configuraciones")
    st.markdown('</div>', unsafe_allow_html=True)
    if reset_todo_superior:
        reset_all()
        st.success("Todas las reinversiones han sido reiniciadas")
        st.rerun()

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
    st.markdown("<div class='linea-divisoria'></div>", unsafe_allow_html=True)
    st.subheader("Regulación")
    
    meses_sin_cobros_inicial = st.number_input(
        "Meses sin cobros:", 
        min_value=0, 
        value=6, 
        step=1,
        key="meses_sin_cobros_inicial",
        help="Tiempo en meses entre el fin de cuotas normales y el inicio de cuotas de regulación"
    )
    
    cuotas_regulacion_inicial = st.number_input(
        "Cuotas Regulación:", 
        min_value=0, 
        value=5, 
        step=1,
        key="cuotas_regulacion_inicial",
        help="Número de cuotas adicionales para el cobro de honorarios por regulación"
    )
    
    importe_regulacion_inicial = st.number_input(
        "Importe Cuota Regulación:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="importe_regulacion_inicial",
        help="Importe bruto de cada cuota de honorarios por regulación (antes de aplicar % de distribución)"
    )
    
    # Usar radio buttons para el % de Distribución
    st.write("% Distribución Regulación:")
    pct_distribucion_inicial = st.radio(
        "",
        options=[20, 40, 60, 80],
        index=1,  # Predeterminado 40% (índice 1)
        horizontal=True,
        key="pct_distribucion_inicial",
        help="Porcentaje del importe de regulación que corresponde al estudio (el resto va al cliente)"
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
    
    # Mover el campo de meses de demora aquí (antes de la divisoria)
    meses_demora_inicial = st.number_input(
        "Meses Hasta Primer Cobro:", 
        min_value=0, 
        value=0, 
        step=1,
        key="meses_demora_inicial",
        help="Tiempo que transcurre desde la inversión hasta recibir el primer pago"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
        ejecutar_inversion = st.button("Ejecutar Inversión Inicial", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
        reset_inicial = st.button("Reset Inicial", type="secondary")
        if reset_inicial:
            reset_all()
            st.success("Inversión inicial y reinversiones reiniciados")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown("<div class='linea-divisoria'></div>", unsafe_allow_html=True)
    st.subheader("Regulación")
    
    meses_sin_cobros_compra = st.number_input(
        "Meses sin cobros:", 
        min_value=0, 
        value=6, 
        step=1,
        key="meses_sin_cobros_compra",
        help="Tiempo en meses entre el fin de cuotas normales y el inicio de cuotas de regulación"
    )
    
    cuotas_regulacion_compra = st.number_input(
        "Cuotas Regulación:", 
        min_value=0, 
        value=5, 
        step=1,
        key="cuotas_regulacion_compra",
        help="Número de cuotas adicionales para el cobro de honorarios por regulación"
    )
    
    importe_regulacion_compra = st.number_input(
        "Importe Cuota Regulación:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="importe_regulacion_compra",
        help="Importe bruto de cada cuota de honorarios por regulación (antes de aplicar % de distribución)"
    )
    
    # Usar radio buttons para el % de Distribución
    st.write("% Distribución Regulación:")
    pct_distribucion_compra = st.radio(
        "",
        options=[20, 40, 60, 80],
        index=1,  # Predeterminado 40% (índice 1)
        horizontal=True,
        key="pct_distribucion_compra",
        help="Porcentaje del importe de regulación que corresponde al estudio (el resto va al cliente)"
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
    
    # Mover el campo de meses de demora aquí (antes de la divisoria)
    meses_demora_compra = st.number_input(
        "Meses Hasta Primer Cobro:", 
        min_value=0, 
        value=0, 
        step=1,
        key="meses_demora_compra",
        help="Tiempo que transcurre desde la inversión hasta recibir el primer pago"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
        reset_compra = st.button("Reset Compra", type="secondary")
        if reset_compra:
            reset_reinversion("Compra")
            st.success("Reinversiones Compra reiniciadas")
        st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown("<div class='linea-divisoria'></div>", unsafe_allow_html=True)
    st.subheader("Regulación")
    
    meses_sin_cobros_colocacion = st.number_input(
        "Meses sin cobros:", 
        min_value=0, 
        value=6, 
        step=1,
        key="meses_sin_cobros_colocacion",
        help="Tiempo en meses entre el fin de cuotas normales y el inicio de cuotas de regulación"
    )
    
    cuotas_regulacion_colocacion = st.number_input(
        "Cuotas Regulación:", 
        min_value=0, 
        value=5, 
        step=1,
        key="cuotas_regulacion_colocacion",
        help="Número de cuotas adicionales para el cobro de honorarios por regulación"
    )
    
    importe_regulacion_colocacion = st.number_input(
        "Importe Cuota Regulación:", 
        min_value=0, 
        value=500000, 
        step=100000,
        key="importe_regulacion_colocacion",
        help="Importe bruto de cada cuota de honorarios por regulación (antes de aplicar % de distribución)"
    )
    
    # Usar radio buttons para el % de Distribución
    st.write("% Distribución Regulación:")
    pct_distribucion_colocacion = st.radio(
        "",
        options=[20, 40, 60, 80],
        index=1,  # Predeterminado 40% (índice 1)
        horizontal=True,
        key="pct_distribucion_colocacion",
        help="Porcentaje del importe de regulación que corresponde al estudio (el resto va al cliente)"
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
    
    # Mover el campo de meses de demora aquí (antes de la divisoria)
    meses_demora_colocacion = st.number_input(
        "Meses Hasta Primer Cobro:", 
        min_value=0, 
        value=0, 
        step=1,
        key="meses_demora_colocacion",
        help="Tiempo que transcurre desde la inversión hasta recibir el primer pago"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="boton-accion boton-reinversion-auto">', unsafe_allow_html=True)
        reinversion_auto = st.button("Reinversión Automática")
        if reinversion_auto:
            # Ejecutar la reinversión automática
            reinversiones_agregadas = ejecutar_reinversion_automatica(
                inversion_colocacion,
                costo_op_colocacion,
                cuotas_colocacion,
                importe_colocacion,
                meses_sin_cobros_colocacion,
                cuotas_regulacion_colocacion,
                importe_regulacion_colocacion,
                pct_distribucion_colocacion,
                no_cobro_colocacion,
                meses_demora_colocacion,
                meses_pago,
                meses_total
            )
            if reinversiones_agregadas > 0:
                st.success(f"Se agregaron {reinversiones_agregadas} reinversiones automáticas")
            else:
                st.warning("No hay fondos suficientes para hacer reinversiones automáticas")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="boton-accion">', unsafe_allow_html=True)
        reset_colocacion = st.button("Reset Colocación", type="secondary")
        if reset_colocacion:
            reset_reinversion("Colocacion")
            st.success("Reinversiones Colocación reiniciadas")
        st.markdown('</div>', unsafe_allow_html=True)

# Generar y mostrar el flujo de caja
if ejecutar_inversion or agregar_compra or agregar_colocacion or reinversion_auto or st.session_state.reinversiones_compra or st.session_state.reinversiones_colocacion:
    st.header("Flujo de Caja")
    
    # Resumen de reinversiones si hay alguna
    if st.session_state.reinversiones_compra or st.session_state.reinversiones_colocacion:
        st.subheader("Resumen de Reinversiones")
        resumen_col1, resumen_col2 = st.columns(2)
        
        with resumen_col1:
            st.write(f"Reinversiones Compra: {len(st.session_state.reinversiones_compra)}")
        
        with resumen_col2:
            # Contar reinversiones manuales y automáticas
            reinv_manuales = sum(1 for r in st.session_state.reinversiones_colocacion if not r.get('automatica', False))
            reinv_automaticas = sum(1 for r in st.session_state.reinversiones_colocacion if r.get('automatica', False))
            st.write(f"Reinversiones Colocación: {len(st.session_state.reinversiones_colocacion)} (Manuales: {reinv_manuales}, Automáticas: {reinv_automaticas})")
    
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
        reinversiones_colocacion=st.session_state.reinversiones_colocacion,
        pago_mensual=pago_mensual,
        meses_pago=meses_pago,
        meses_total=meses_total
    )
    
    # Formatear valores
    for col in ["Ingresos", "Reinversión", "Pago Mensual", "Total Cobrado", "Saldo Acumulado", "Total Disponible", "No Cobro"]:
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
