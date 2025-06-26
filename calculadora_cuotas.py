import streamlit as st
import pandas as pd
import numpy_financial as npf

logo_base64 = '''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'''

@st.cache_data
def cargar_tarifario():
    df = pd.read_excel("Tarifario de Tasas BU.xlsx")
    df['Tipo de Producto'] = df['Tipo de Producto'].str.strip()
    df['GARANTIA'] = df['GARANTIA'].str.strip()
    return df

df_tarifario = cargar_tarifario()

def buscar_condiciones(producto, garantia, monto):
    condiciones = df_tarifario[(df_tarifario['Tipo de Producto'].str.lower() == producto.lower()) &
        (df_tarifario['GARANTIA'].str.lower() == garantia.lower()) &
        (df_tarifario['Monto Minimo Solicitado'] <= monto) &
        (df_tarifario['Monto Maximo Solicitado'] >= monto)]
    return condiciones.iloc[0] if not condiciones.empty else None

def calcular_cuota(monto, plazo_meses, tasa_mensual):
    cuota = npf.pmt(tasa_mensual, plazo_meses, -monto)
    return round(cuota, 2)

st.set_page_config(page_title='Calculadora BU', layout='centered')
st.markdown('''
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
''', unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align:center;'>
<img src='data:image/png;base64,{logo_base64}' width='300'/>
</div>""", unsafe_allow_html=True)
st.markdown("<h2 style='color:#B7B6B5; font-weight:600; text-align:center;'>Calculadora de Cuotas - Banco Unión</h2>", unsafe_allow_html=True)

tipo = st.selectbox("Tipo de Préstamo", df_tarifario['Tipo de Producto'].unique())
garantia = st.selectbox("Tipo de Garantía", df_tarifario['GARANTIA'].unique())
monto = st.number_input("Monto solicitado (RD$)", min_value=0, step=1000, format="%d")
plazo = st.number_input("Plazo en meses", min_value=1, max_value=120, step=1, value=None)

if st.button("Calcular Cuota"):
    condiciones_existentes = df_tarifario[(df_tarifario['Tipo de Producto'].str.lower() == tipo.lower()) &
        (df_tarifario['GARANTIA'].str.lower() == garantia.lower())]
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
                    cuota = calcular_cuota(monto, plazo, tasa)
                    gastos_cierre = monto * tasa_gastos
                    st.success(f"Cuota mensual: RD${cuota:,.2f}")
                    st.info(f"Gastos de cierre: RD${gastos_cierre:,.2f}")
                    st.markdown(f"**Tasa de interés anual:** {tasa_anual*100:.2f}%")
                    st.markdown(f"**Porcentaje de gastos de cierre:** {tasa_gastos*100:.2f}%")
                else:
                    st.warning(f"El plazo ingresado excede el máximo permitido para este tipo de préstamo y monto. El plazo máximo permitido es {int(plazo_maximo)} meses.")
            else:
                st.error("No hay condiciones para este monto o tipo de préstamo.")
