import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import base64

st.title("ReportLab Test – PDF Generator")

# PDF erzeugen
from fpdf import FPDF
import io
import base64

def build_pdf_fpdf(df_filtered, chart_png, name_filter):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Pain Tracking Bericht", ln=True, align="L")
    subtitle = f"Filter: Name enthält '{name_filter}'" if name_filter else "Filter: keiner"
    pdf.cell(200, 10, txt=subtitle, ln=True, align="L")
    pdf.cell(200, 10, txt=f"Generiert am {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="L")

    # Diagramm einfügen
    chart_path = "chart_temp.png"
    with open(chart_path, "wb") as f:
        f.write(chart_png.getbuffer())
    pdf.image(chart_path, x=10, y=40, w=180)

    pdf.set_y(130)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Daten (gefiltert):", ln=True)

    if df_filtered.empty:
        pdf.cell(200, 10, txt="Keine Daten vorhanden.", ln=True)
    else:
        for _, row in df_filtered.iterrows():
            line = " | ".join(str(row.get(col, "")) for col in DEFAULT_COLUMNS)
            pdf.multi_cell(0, 8, txt=line)

    # PDF als Bytes zurückgeben
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output
.decode("utf-8")
pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
st.markdown(pdf_display, unsafe_allow_html=True)


































