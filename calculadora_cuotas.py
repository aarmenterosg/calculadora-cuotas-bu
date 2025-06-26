import streamlit as st
import pandas as pd
import numpy_financial as npf
from PIL import Image

# Cargar el logo
logo = Image.open("BU_LOGO.png")

# Cargar el tarifario
@st.cache_data
def cargar_tarifario():
    df = pd.read_excel("Tarifario de Tasas BU.xlsx")
    df['Tipo de Producto'] = df['Tipo de Producto'].str.strip()
    df['GARANTIA'] = df['GARANTIA'].str.strip()
    return df

df_tarifario = cargar_tarifario()

def buscar_condiciones(producto, garantia, monto):
    condiciones = df_tarifario[
        (df_tarifario['Tipo de Producto'].str.lower() == producto.lower()) &
        (df_tarifario['GARANTIA'].str.lower() == garantia.lower()) &
        (df_tarifario['Monto Minimo Solicitado'] <= monto) &
        (df_tarifario['Monto Maximo Solicitado'] >= monto)
    ]
    return condiciones.iloc[0] if not condiciones.empty else None

def calcular_cuota(monto, plazo_meses, tasa_mensual):
    cuota = npf.pmt(tasa_mensual, plazo_meses, -monto)
    return round(cuota, 2)

# Estilo personalizado optimizado para móvil
st.set_page_config(page_title="Calculadora BU", layout="centered")
st.markdown("""
    <style>
    .stApp {
        background-color: #f9f9f9;
        font-family: 'Segoe UI', sans-serif;
        padding: 1em;
    }
    .stButton>button {
        background-color: #F03C2E;
        color: white;
        border-radius: 6px;
        padding: 0.6em 1em;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #d63324;
    }
    input[type="text"] {
        font-weight: bold;
        color: #333;
        width: 100%;
    }
    .element-container:has(.stTextInput) label,
    .element-container:has(.stSelectbox) label,
    .element-container:has(.stNumberInput) label {
        font-size: 1.1rem;
        color: #444;
    }
    @media only screen and (max-width: 600px) {
        h2 {
            font-size: 1.5rem;
            text-align: center;
        }
        img {
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado con logo y título
import base64
from pathlib import Path
logo_base64 = base64.b64encode(Path("BU_LOGO.png").read_bytes()).decode()
st.markdown(
    f"<div style='text-align:center;'><img src='data:image/png;base64,{logo_base64}' width='300'/></div>",
    unsafe_allow_html=True
)
st.markdown("<h2 style='color:#B7B6B5; font-weight:600; text-align:center;'>Calculadora de Cuotas - Banco Unión</h2>", unsafe_allow_html=True)

# Entradas del usuario
tipo = st.radio("Tipo de Préstamo", df_tarifario['Tipo de Producto'].unique())
garantia = st.radio("Tipo de Garantía", df_tarifario['GARANTIA'].unique())

# Campo de entrada numérica para monto solicitado
monto = st.number_input("Monto solicitado (RD$)", min_value=0, step=1000, format="%d")
plazo = st.number_input("Plazo en meses", min_value=1, max_value=120, step=1, value=None)

if st.button("Calcular Cuota"):
    condiciones_existentes = df_tarifario[
        (df_tarifario['Tipo de Producto'] == tipo) &
        (df_tarifario['GARANTIA'] == garantia)
    ]
    if condiciones_existentes.empty:
        st.warning("No hay condiciones definidas para este tipo de préstamo y garantía.")
    else:
        monto_min = condiciones_existentes['Monto Minimo Solicitado'].min()
        if monto == 0 or plazo == 0:
            st.warning("Por favor ingresa un monto y plazo válidos antes de calcular la cuota.")
        elif monto < monto_min:
            st.warning(f"El monto ingresado es menor al mínimo permitido ({int(monto_min):,} RD$) para este tipo de préstamo.")
        else:
            condiciones = buscar_condiciones(tipo, garantia, monto)
            if condiciones is not None:
                plazo_maximo = condiciones['Plazo Maximo (meses)']
                if plazo <= plazo_maximo:
                    tasa_anual = condiciones['Tasa']
                    tasa = (1 + tasa_anual) ** (1 / 12) - 1
                    tasa_gastos = condiciones['Gastos de Cierre']
                    monto_total = monto + (monto * tasa_gastos)
                    cuota = calcular_cuota(monto_total, plazo, tasa)
                    gastos_cierre = monto * tasa_gastos

                    st.success(f"Cuota mensual: RD${cuota:,.2f} (incluye gastos de cierre)")
                    st.info(f"Gastos de cierre: RD${gastos_cierre:,.2f}")
                    st.markdown(f"**Tasa de interés anual:** {tasa_anual*100:.2f}%")
                    st.markdown(f"**Porcentaje de gastos de cierre:** {tasa_gastos*100:.2f}%")

                    # Tabla de amortización
                    from datetime import datetime
                    from dateutil.relativedelta import relativedelta
                    saldo = monto_total
                    fecha_inicio = datetime.today()
                    tabla = []
                    for i in range(1, plazo + 1):
                        interes = round(saldo * tasa, 2)
                        capital = round(cuota - interes, 2)
                        saldo = round(saldo - capital, 2)
                        fecha = fecha_inicio + relativedelta(months=i)
                        tabla.append({
                            "Cuota #": i,
                            "Fecha": fecha.strftime("%d/%m/%Y"),
                            "Capital": capital,
                            "Interés": interes,
                            "Cuota Total": cuota,
                            "Saldo": saldo if saldo > 0 else 0
                        })
                    df_tabla = pd.DataFrame(tabla)
                    df_tabla[['Capital', 'Interés', 'Cuota Total', 'Saldo']] = df_tabla[['Capital', 'Interés', 'Cuota Total', 'Saldo']].applymap(lambda x: f"RD${int(round(x)):,}")
                    st.markdown("### Tabla de Amortización")
                    st.dataframe(df_tabla, use_container_width=True)

                    # Botón para descargar en Excel
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_tabla.to_excel(writer, index=False, sheet_name='Amortizacion')
                    datos_excel = output.getvalue()

                    st.download_button(
                        label="📥 Descargar tabla en Excel",
                        data=datos_excel,
                        file_name="tabla_amortizacion.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning(f"El plazo ingresado excede el máximo permitido para este tipo de préstamo y monto. "
                               f"El plazo máximo permitido es {int(plazo_maximo)} meses.")
            else:
                st.error("No hay condiciones para este monto o tipo de préstamo.")
