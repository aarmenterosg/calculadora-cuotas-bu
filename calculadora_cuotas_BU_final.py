
import streamlit as st
import pandas as pd
import numpy_financial as npf
from PIL import Image
import base64
from pathlib import Path
from datetime import datetime
import io
from dateutil.relativedelta import relativedelta

# Cargar logo
logo = Image.open("BU_LOGO.png")
logo_base64 = base64.b64encode(Path("BU_LOGO.png").read_bytes()).decode()

# Cargar tarifario
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

# Estilo
st.set_page_config(page_title="Calculadora BU", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; font-family: 'Segoe UI'; padding: 1em; }
    .stButton>button {
        background-color: #F03C2E; color: white; border-radius: 6px;
        padding: 0.6em 1em; border: none; width: 100%;
    }
    .stButton>button:hover { background-color: #d63324; }
    @media only screen and (max-width: 600px) {
        h2 { font-size: 1.5rem; text-align: center; }
        img { display: block; margin-left: auto; margin-right: auto; }
    }
    </style>
""", unsafe_allow_html=True)

# Logo
st.markdown(f"<div style='text-align:center;'><img src='data:image/png;base64,{logo_base64}' width='300'/></div>", unsafe_allow_html=True)
st.markdown("<h2 style='color:#B7B6B5; font-weight:600; text-align:center;'>Calculadora de Cuotas - Banco Unión</h2>", unsafe_allow_html=True)

# Datos del cliente
st.subheader("Datos del Cliente")
cedula = st.text_input("Cédula")
nombre = st.text_input("Nombre completo")
telefono = st.text_input("Teléfono")

st.subheader("Parámetros del Préstamo")
tipo = st.radio("Tipo de Préstamo", df_tarifario['Tipo de Producto'].unique())
garantia = st.radio("Tipo de Garantía", df_tarifario['GARANTIA'].unique())
monto = st.number_input("Monto solicitado (RD$)", min_value=0, step=1000, format="%d")
plazo = st.number_input("Plazo en meses", min_value=1, max_value=120, step=1, value=None)

if st.button("Calcular Cuota"):
    if not cedula or not nombre or not telefono:
        st.warning("Por favor completa todos los datos del cliente antes de continuar.")
    else:
        condiciones_existentes = df_tarifario[
            (df_tarifario['Tipo de Producto'] == tipo) &
            (df_tarifario['GARANTIA'] == garantia)
        ]
        if condiciones_existentes.empty:
            st.warning("No hay condiciones definidas para este tipo de préstamo y garantía.")
        else:
            monto_min = condiciones_existentes['Monto Minimo Solicitado'].min()
            if monto == 0 or plazo == 0:
                st.warning("Por favor ingresa un monto y plazo válidos.")
            elif monto < monto_min:
                st.warning(f"El monto ingresado es menor al mínimo permitido ({int(monto_min):,} RD$).")
            else:
                condiciones = buscar_condiciones(tipo, garantia, monto)
                if condiciones is not None:
                    tasa_anual = condiciones['Tasa']
                    tasa_gastos = condiciones['Gastos de Cierre']
                    plazo_maximo = condiciones['Plazo Maximo (meses)']
                    tipo_tasa = condiciones.get('Tipo de Tasa', 'Fija') if 'Tipo de Tasa' in condiciones else 'Fija'
                    if plazo > plazo_maximo:
                        st.warning(f"El plazo máximo permitido es {int(plazo_maximo)} meses.")
                    else:
                        tasa = (1 + tasa_anual) ** (1 / 12) - 1
                        monto_total = monto + (monto * tasa_gastos)
                        cuota = calcular_cuota(monto_total, plazo, tasa)
                        gastos_cierre = monto * tasa_gastos

                        st.success(f"Cuota mensual: RD${cuota:,.2f} (incluye gastos de cierre)")
                        st.info(f"Gastos de cierre: RD${gastos_cierre:,.2f}")
                        st.markdown(f"**Tasa de interés anual:** {tasa_anual*100:.2f}%")
                        st.markdown(f"**Porcentaje de gastos de cierre:** {tasa_gastos*100:.2f}%")

                        if tipo_tasa.lower() in ['variable', 'promocional']:
        st.warning(f"⚠️ Tasa '{tipo_tasa}' detectada. Ingresa la tasa anual manualmente.")
        tasa_anual_manual = st.number_input("Tasa anual promocional (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
        if tasa_anual_manual > 0:
            tasa_anual = tasa_anual_manual / 100
            tipo_tasa += " - Manual"
    
                            st.warning(f"⚠️ Tasa no fija detectada: '{tipo_tasa}'")

                        # Tabla de amortización
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

                        # Guardar registro en CSV
                        registro = {
                            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Cedula": cedula,
                            "Nombre": nombre,
                            "Telefono": telefono,
                            "Producto": tipo,
                            "Garantia": garantia,
                            "Monto": monto,
                            "Plazo": plazo,
                            "Tasa Anual": tasa_anual,
                            "Tipo de Tasa": tipo_tasa,
                            "Cuota": cuota
                        }
                        df_registro = pd.DataFrame([registro])
                        path_csv = Path("simulaciones_clientes.csv")
                        if path_csv.exists():
                            df_registro.to_csv(path_csv, mode='a', header=False, index=False)
                        else:
                            df_registro.to_csv(path_csv, index=False)

                        # Botón para descargar
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_tabla.to_excel(writer, index=False, sheet_name='Amortizacion')
                        
                        # Generar PDF
                        from fpdf import FPDF

                        class PDF(FPDF):
                            def header(self):
                                self.image("BU_LOGO.png", 10, 8, 50)
                                self.set_font("Arial", "B", 12)
                                self.cell(0, 10, "Simulación de Préstamo - Banco Unión", ln=True, align="C")
                                self.ln(5)

                            def footer(self):
                                self.set_y(-15)
                                self.set_font("Arial", "I", 8)
                                self.set_text_color(128)
                                self.cell(0, 10, "www.bancounion.com.do | @bancounionrd", align="C")

                        pdf = PDF(orientation='L', unit='mm', format='A4')
                        pdf.add_page()
                        pdf.set_font("Arial", "", 11)
                        pdf.cell(0, 10, f"Nombre: {nombre}", ln=True)
                        pdf.cell(0, 10, f"Cédula: {cedula}", ln=True)
                        pdf.cell(0, 10, f"Teléfono: {telefono}", ln=True)
                        pdf.cell(0, 10, f"Producto: {tipo} | Garantía: {garantia}", ln=True)
                        pdf.cell(0, 10, f"Monto: RD${monto:,.2f} | Plazo: {plazo} meses | Tasa Anual: {tasa_anual*100:.2f}%", ln=True)
                        pdf.cell(0, 10, f"Cuota mensual estimada: RD${cuota:,.2f}", ln=True)
                        pdf.ln(10)
                        pdf.set_fill_color(240, 240, 240)
                        pdf.set_font("Arial", "B", 10)
                        col_widths = [25, 40, 40, 40, 40]
                        cols = list(df_tabla.columns)
                        for i, col in enumerate(cols):
                            pdf.cell(col_widths[i], 8, col, 1, 0, 'C', 1)
                        pdf.ln()
                        pdf.set_font("Arial", "", 9)
                        for _, row in df_tabla.iterrows():
                            for i, val in enumerate(row):
                                pdf.cell(col_widths[i], 8, str(val), 1, 0, 'C')
                            pdf.ln()
                        pdf_path = "simulacion_prestamo_BU.pdf"
                        pdf.output(pdf_path)
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="📄 Descargar tabla en PDF",
                                data=f,
                                file_name=pdf_path,
                                mime="application/pdf"
                            )

                        # Generar link WhatsApp
                        mensaje = (
                            f"Hola {nombre}, te compartimos tu simulación de préstamo por RD${monto:,.0f} "
                            f"a {plazo} meses. Adjuntamos el PDF con la tabla de amortización. "
                            "¡Gracias por preferirnos!"
                        )
                        mensaje_encoded = mensaje.replace(" ", "%20").replace(",", "%2C")
                        whatsapp_link = f"https://wa.me/1{telefono}?text={mensaje_encoded}"
                        st.markdown(f"[📲 Enviar por WhatsApp]({whatsapp_link})", unsafe_allow_html=True)

                        st.download_button(
                            label="📥 Descargar tabla en Excel",
                            data=output.getvalue(),
                            file_name="tabla_amortizacion.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("No hay condiciones para este monto o tipo de préstamo.")
