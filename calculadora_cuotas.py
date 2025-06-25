
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

def calcular_amortizacion(monto, plazo_meses, tasa_mensual):
    cuota = npf.pmt(tasa_mensual, plazo_meses, -monto)
    tabla = []
    saldo = monto
    for mes in range(1, plazo_meses + 1):
        interes = saldo * tasa_mensual
        abono_capital = cuota - interes
        saldo -= abono_capital
        tabla.append({
            "Mes": mes,
            "Cuota": round(cuota, 2),
            "Interés": round(interes, 2),
            "Abono a Capital": round(abono_capital, 2),
            "Saldo": round(max(saldo, 0), 2)
        })
    return round(cuota, 2), round(monto * tasa_gastos, 2), pd.DataFrame(tabla)

# Estilo personalizado
st.set_page_config(page_title="Calculadora BU", layout="centered")
st.markdown("""
    <style>
    .stApp {
        background-color: #f9f9f9;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #F03C2E;
        color: white;
        border-radius: 6px;
        padding: 0.4em 1em;
        border: none;
    }
    .stButton>button:hover {
        background-color: #d63324;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado con logo y título
st.image(logo, width=300)
st.markdown("<h2 style='color:#B7B6B5; font-weight:600;'>Calculadora de Cuotas - Banco Unión</h2>", unsafe_allow_html=True)

# Entradas del usuario
tipo = st.selectbox("Tipo de Préstamo", df_tarifario['Tipo de Producto'].unique())
garantia = st.selectbox("Tipo de Garantía", df_tarifario['GARANTIA'].unique())
monto = st.number_input("Monto solicitado (RD$)", min_value=1000, step=1000)
plazo = st.number_input("Plazo en meses", min_value=1, max_value=120, step=1)

if st.button("Calcular Cuota"):
    condiciones = buscar_condiciones(tipo, garantia, monto)

    if condiciones is not None and plazo <= condiciones['Plazo Maximo (meses)']:
        tasa_anual = condiciones['Tasa']
        tasa = (1 + tasa_anual) ** (1 / 12) - 1
        tasa_gastos = condiciones['Gastos de Cierre']
        cuota, gastos_cierre, amortizacion = calcular_amortizacion(monto, plazo, tasa)

        st.success(f"Cuota mensual: RD${cuota:,.2f}")
        st.info(f"Gastos de cierre: RD${gastos_cierre:,.2f}")

        st.subheader("Tabla de Amortización")
        st.dataframe(amortizacion, use_container_width=True)
        st.download_button("Descargar tabla en Excel", amortizacion.to_csv(index=False).encode(),
                           file_name="tabla_amortizacion.csv", mime="text/csv")
    else:
        st.error("No hay condiciones para este monto o el plazo excede el permitido.")
