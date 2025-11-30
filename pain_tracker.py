import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# ⚙️ Seiteneinstellungen
st.set_page_config(page_title="Schmerzverlauf", layout="centered")

# 🔐 Passwortschutz
try:
    PASSWORT = st.secrets["app_password"]
except Exception:
    st.error("⚠️ Kein Passwort in st.secrets gesetzt.")
    st.stop()

if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False

# 📂 CSV-Dateien
CSV_DATEI = "schmerzverlauf.csv"
BACKUP_DATEI = "schmerzverlauf_backup.csv"

# 🛡️ Selbstcheck
SPALTEN = [
    "Uhrzeit","Name","Medikament","Körperregion","Dosierung",
    "Schmerzempfinden","Einheit","NRS","Zeitpunkt","Tageszeit","Notizen"
]

if os.path.exists(CSV_DATEI):
    try:
        df = pd.read_csv(CSV_DATEI)
        fehlende = [s for s in SPALTEN if s not in df.columns]
        if fehlende:
            st.warning(f"⚠️ Fehlende Spalten: {fehlende}")
            for spalte in fehlende:
                df[spalte] = ""
        st.success(f"✅ {len(df)} Einträge geladen.")
        df.to_csv(BACKUP_DATEI, index=False)
        st.info("📂 Backup gespeichert als 'schmerzverlauf_backup.csv'")
    except Exception as e:
        st.error(f"❌ Fehler beim Laden: {e}")
        df = pd.DataFrame(columns=SPALTEN)
else:
    st.warning("⚠️ Keine CSV gefunden – neue wird erstellt.")
    df = pd.DataFrame(columns=SPALTEN)
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

# 📊 Tabs
tab1, tab2, tab3 = st.tabs(["Eingabe", "Daten & Filter", "Verwaltung"])

# 📝 Tab 1: Eingabe
with tab1:
    st.header("Schmerzverlauf erfassen")

    with st.form("eingabe_formular"):
        name = st.text_input("Name")
        medikament = st.text_input("Medikament")
        region = st.text_input("Körperregion")
        dosierung = st.text_input("Dosierung")
        empfinden = st.text_input("Schmerzempfinden")
        einheit = st.text_input("Einheit")
        nrs = st.number_input("NRS (0–10)", min_value=0, max_value=10, step=1)
        zeitpunkt = st.text_input("Zeitpunkt")
        tageszeit = st.text_input("Tageszeit")
        notizen = st.text_area("Notizen")
        uhrzeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        submitted = st.form_submit_button("➕ Eintrag speichern")
        if submitted:
            neuer_eintrag = pd.DataFrame([{
                "Uhrzeit": uhrzeit,
                "Name": name,
                "Medikament": medikament,
                "Körperregion": region,
                "Dosierung": dosierung,
                "Schmerzempfinden": empfinden,
                "Einheit": einheit,
                "NRS": nrs,
                "Zeitpunkt": zeitpunkt,
                "Tageszeit": tageszeit,
                "Notizen": notizen
            }])
            df = pd.concat([df, neuer_eintrag], ignore_index=True)
            df.to_csv(CSV_DATEI, index=False)
            st.success("✅ Eintrag gespeichert")
            st.rerun()

# 🎛️ Tab 2: Filter & Diagramm
with tab2:
    st.header("Daten filtern und visualisieren")

    def dropdown(spalte):
        return st.selectbox(spalte, ["Alle"] + sorted(df[spalte].dropna().unique())) if spalte in df.columns else "Alle"

    name_filter = dropdown("Name")
    region_filter = dropdown("Körperregion")
    medikament_filter = dropdown("Medikament")
    tageszeit_filter = dropdown("Tageszeit")

    gefiltert = df.copy()
    if name_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Name"] == name_filter]
    if region_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Körperregion"] == region_filter]
    if medikament_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Medikament"] == medikament_filter]
    if tageszeit_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Tageszeit"] == tageszeit_filter]

    st.dataframe(gefiltert)

    if "NRS" in gefiltert.columns and not gefiltert.empty:
        fig, ax = plt.subplots()
        ax.plot(gefiltert.index, gefiltert["NRS"], marker="o")
        ax.set_xlabel("Eintrag")
        ax.set_ylabel("NRS")
        ax.set_title(f"Schmerzverlauf von {name_filter if name_filter != 'Alle' else 'Auswahl'}")
        st.pyplot(fig)
    else:
        st.info("Kein NRS-Verlauf darstellbar.")

# 🗂️ Tab 3: Verwaltung
with tab3:
    st.header("Verwaltung")

    if st.button("CSV neu laden"):
        df = pd.read_csv(CSV_DATEI)
        st.success("CSV neu geladen ✅")
        st.dataframe(df)

    if st.button("Alle Daten löschen"):
        df = pd.DataFrame(columns=SPALTEN)
        df.to_csv(CSV_DATEI, index=False)
        st.warning("⚠️ Alle Daten gelöscht")
        st.rerun()

    st.download_button(
        label="📥 CSV herunterladen",
        data=open(CSV_DATEI, "rb").read(),
        file_name="schmerzverlauf.csv",
        mime="text/csv"
    )











