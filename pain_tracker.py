import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import base64

st.title("ReportLab Test – PDF Generator")

# PDF erzeugen
buffer = io.BytesIO()
c = canvas.Canvas(buffer, pagesize=A4)
c.setFont("Helvetica", 14)
c.drawString(100, 750, "Hallo Michael – ReportLab funktioniert!")
c.save()
buffer.seek(0)

# Download-Button
st.download_button(
    "PDF herunterladen",
    data=buffer,
    file_name="reportlab_test.pdf",
    mime="application/pdf"
)

# PDF direkt anzeigen
pdf_bytes = buffer.getvalue()
b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
st.markdown(pdf_display, unsafe_allow_html=True)

































