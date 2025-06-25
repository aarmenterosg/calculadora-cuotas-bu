
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
st.image(logo, width=220)
st.markdown("<h2 style='color:#B7B6B5; font-weight:600; text-align:center;'>Calculadora de Cuotas - Banco Unión</h2>", unsafe_allow_html=True)

# Entradas del usuario
tipo = st.selectbox("Tipo de Préstamo", df_tarifario['Tipo de Producto'].unique())
garantia = st.selectbox("Tipo de Garantía", df_tarifario['GARANTIA'].unique())

# Campo de texto con formato preestablecido para monto
monto_str = st.text_input("Monto solicitado (RD$)", value="")

try:
    monto = int(monto_str.replace(",", "").replace("RD$", "").replace("$", "").strip())
except ValueError:
    monto = 0

plazo = st.number_input("Plazo en meses", min_value=1, max_value=120, step=1, value=None)

if st.button("Calcular Cuota"):
    condiciones_existentes = df_tarifario[
        (df_tarifario['Tipo de Producto'].str.lower() == tipo.lower()) &
        (df_tarifario['GARANTIA'].str.lower() == garantia.lower())
    ]
    if condiciones_existentes.empty:
        st.warning("No hay condiciones definidas para este tipo de préstamo y garantía.")
    else:
        monto_min = condiciones_existentes['Monto Minimo Solicitado'].min()
        if monto == 0 or plazo is None or plazo == 0:
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
                    cuota = calcular_cuota(monto, plazo, tasa)
                    gastos_cierre = monto * tasa_gastos

                    st.success(f"Cuota mensual: RD${cuota:,.2f}")
                    st.info(f"Gastos de cierre: RD${gastos_cierre:,.2f}")
                    st.markdown(f"**Tasa de interés anual:** {tasa_anual*100:.2f}%")
                    st.markdown(f"**Porcentaje de gastos de cierre:** {tasa_gastos*100:.2f}%")
                else:
                    st.warning(f"El plazo ingresado excede el máximo permitido para este tipo de préstamo y monto. "
                               f"El plazo máximo permitido es {int(plazo_maximo)} meses.")
            else:
                st.error("No hay condiciones para este monto o tipo de préstamo.")
