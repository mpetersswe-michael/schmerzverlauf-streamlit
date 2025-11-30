import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
from io import BytesIO
from docx import Document

# ⚙️ Seiteneinstellungen
st.set_page_config(page_title="Schmerzverlauf", layout="centered")

# 🔐 Passwortschutz über st.secrets
try:
    PASSWORT = st.secrets["app_password"]
except Exception:
    st.error("⚠️ Kein Passwort in st.secrets gesetzt. Bitte im Secrets-Manager hinterlegen.")
    st.stop()

if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False

# 📂 CSV-Dateien
CSV_DATEI = "schmerzverlauf.csv"
BACKUP_DATEI = "schmerzverlauf_backup.csv"

# 🛡️ Selbstcheck-Routine
if os.path.exists(CSV_DATEI):
    try:
        df = pd.read_csv(CSV_DATEI)
        if df.empty:
            st.warning("⚠️ CSV-Datei ist leer – keine Daten gefunden.")
        else:
            st.success(f"✅ {len(df)} Einträge geladen.")
            df.to_csv(BACKUP_DATEI, index=False)
            st.info("📂 Backup gespeichert als 'schmerzverlauf_backup.csv'")
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der CSV: {e}")
        df = pd.DataFrame(columns=[
            "Uhrzeit", "Name", "Region", "Schmerzempfinden", "Intensität", "Medikament"
        ])
else:
    st.warning("⚠️ Keine CSV-Datei gefunden – neue wird erstellt.")
    df = pd.DataFrame(columns=[
        "Uhrzeit", "Name", "Region", "Schmerzempfinden", "Intensität", "Medikament"
    ])
    df.to_csv(CSV_DATEI, index=False)

# 🚪 Sidebar: Login/Logout
with st.sidebar:
    st.markdown("### Zugang")
    if st.session_state.eingeloggt:
        st.success("✅ Eingeloggt als Michael")
        if st.button("🚪 Logout"):
            st.session_state.eingeloggt = False
            st.toast("Erfolgreich ausgeloggt ✅")
            st.rerun()
    else:
        st.warning("🔒 Nicht eingeloggt")

# 🔐 Login-Fenster
if not st.session_state.eingeloggt:
    st.title("🔐 Login erforderlich")
    pw = st.text_input("Passwort eingeben:", type="password")
    if pw and pw == PASSWORT:
        st.session_state.eingeloggt = True
        st.toast("Login erfolgreich ✅")
        st.rerun()
    elif pw and pw != PASSWORT:
        st.error("❌ Falsches Passwort")
    st.stop()

# -------------------------
# 📊 Tabs für App-Inhalte
# -------------------------
tab1, tab2, tab3 = st.tabs(["Eingabe", "Daten & Filter", "Verwaltung"])

# 📝 Tab 1: Eingabe
with tab1:
    st.header("Schmerzverlauf erfassen")

    with st.form("eingabe_formular"):
        name = st.text_input("Name (Patient)")
        medikament = st.text_input("Medikament")
        region = st.text_input("Körperregion")
        empfinden = st.text_input("Schmerzempfinden")
        intensitaet = st.slider("Intensität (0–10)", min_value=0, max_value=10, step=1)
        uhrzeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        submitted = st.form_submit_button("➕ Eintrag speichern")
        if submitted:
            neuer_eintrag = pd.DataFrame([{
                "Uhrzeit": uhrzeit,
                "Name": name,
                "Region": region,
                "Schmerzempfinden": empfinden,
                "Intensität": intensitaet,
                "Medikament": medikament
            }])
            df = pd.concat([df, neuer_eintrag], ignore_index=True)
            df.to_csv(CSV_DATEI, index=False)
            st.success("✅ Eintrag gespeichert")
            st.rerun()

# 🎛️ Tab 2: Daten & Filter
with tab2:
    st.header("Daten filtern und visualisieren")

    name_filter = st.selectbox("Name auswählen", options=["Alle"] + sorted(df["Name"].dropna().unique().tolist()))
    region_filter = st.selectbox("Region auswählen", options=["Alle"] + sorted(df["Region"].dropna().unique().tolist()))
    medikament_filter = st.selectbox("Medikament auswählen", options=["Alle"] + sorted(df["Medikament"].dropna().unique().tolist()))

    gefiltert = df.copy()
    if name_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Name"] == name_filter]
    if region_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Region"] == region_filter]
    if medikament_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Medikament"] == medikament_filter]

    st.dataframe(gefiltert)

    if not gefiltert.empty:
        fig, ax = plt.subplots()
        ax.plot(gefiltert.index, gefiltert["Intensität"], marker="o")
        ax.set_xlabel("Eintrag")
        ax.set_ylabel("Intensität")
        titel_name = name_filter if name_filter != "Alle" else "Auswahl"
        ax.set_title(f"Schmerzverlauf von {titel_name}")
        st.pyplot(fig)

# 🗂️ Tab 3: Verwaltung
with tab3:
    st.header("Verwaltung")

    if st.button("CSV neu laden"):
        df = pd.read_csv(CSV_DATEI)
        st.success("CSV neu geladen ✅")
        st.dataframe(df)

    if st.button("Alle Daten löschen"):
        df = pd.DataFrame(columns=df.columns)
        df.to_csv(CSV_DATEI, index=False)
        st.warning("⚠️ Alle Daten gelöscht")
        st.rerun()

    # 📥 Download-Button für CSV
    st.download_button(
        label="📥 CSV herunterladen",
        data=open(CSV_DATEI, "rb").read(),
        file_name="schmerzverlauf.csv",
        mime="text/csv"
    )

    # 📘 Word-Dokumentation erstellen
    if st.button("📘 Word-Dokumentation erstellen"):
        doc = Document()
        doc.add_heading("Onboarding & Workflow – Schmerzverlauf App", level=1)

        doc.add_paragraph("✅ Login: Passwort eingeben, Toast bestätigt erfolgreichen Zugang.")
        doc.add_paragraph("✅ Eingabe: Patientendaten, Medikament, Region, Schmerzempfinden, Intensität.")
        doc.add_paragraph("✅ Speicherung: Einträge werden automatisch mit Zeitstempel gesichert.")
        doc.add_paragraph("✅ Filter: Dropdowns für Name, Region, Medikament.")
        doc.add_paragraph("✅ Diagramm: Verlauf der Intensität pro Patient.")
        doc.add_paragraph("✅ Verwaltung: CSV neu laden, Daten löschen, Backup automatisch.")
        doc.add_paragraph("✅ Export: CSV-Download jederzeit möglich.")

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="📘 Word-Dokumentation herunterladen",
            data=buffer,
            file_name="Schmerzverlauf_Dokumentation.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )







