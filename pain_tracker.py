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

# 🛡️ Feste Legacy-Spaltenreihenfolge
SPALTEN = [
    "Name", "Körperregion", "Schmerzempfinden", "NRS",
    "Medikament", "Dosierung", "Einheit",
    "Zeitpunkt", "Tageszeit", "Notizen"
]

def leeres_df():
    return pd.DataFrame(columns=SPALTEN)

# CSV laden oder neu erstellen
if os.path.exists(CSV_DATEI):
    try:
        df = pd.read_csv(CSV_DATEI)
        for s in SPALTEN:
            if s not in df.columns:
                df[s] = ""
        df = df[SPALTEN]
        st.success(f"✅ {len(df)} Einträge geladen.")
        df.to_csv(BACKUP_DATEI, index=False)
        st.info("📂 Backup gespeichert als 'schmerzverlauf_backup.csv'")
    except Exception as e:
        st.error(f"❌ Fehler beim Laden: {e}")
        df = leeres_df()
else:
    st.warning("⚠️ Keine CSV gefunden – neue wird erstellt.")
    df = leeres_df()
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

# 📝 Tab 1: Eingabe (korrekte Legacy-Zuordnung)
with tab1:
    st.header("Schmerzverlauf erfassen")

    with st.form("eingabe_formular"):
        name = st.text_input("Name (Patient)")
        koerperregion = st.text_input("Körperregion")
        schmerzempfinden = st.text_input("Schmerzempfinden")
        nrs = st.number_input("NRS (0–10)", min_value=0, max_value=10, step=1)
        medikament = st.text_input("Medikament")
        dosierung = st.text_input("Dosierung (z. B. 400)")
        einheit = st.text_input("Einheit (z. B. mg, Tablette)")
        # Zeitpunkt automatisch setzen
        zeitpunkt = datetime.now().strftime("%Y-%m-%d")
        tageszeit = st.text_input("Tageszeit")
        notizen = st.text_area("Begleitsymptome / Notizen")

        submitted = st.form_submit_button("➕ Eintrag speichern")
        if submitted:
            neuer_eintrag = pd.DataFrame([{
                "Name": name,
                "Körperregion": koerperregion,
                "Schmerzempfinden": schmerzempfinden,
                "NRS": nrs,
                "Medikament": medikament,
                "Dosierung": dosierung,
                "Einheit": einheit,
                "Zeitpunkt": zeitpunkt,   # automatisch Datum
                "Tageszeit": tageszeit,
                "Notizen": notizen
            }])[SPALTEN]
            df = pd.concat([df, neuer_eintrag], ignore_index=True)
            df.to_csv(CSV_DATEI, index=False)
            st.success("✅ Eintrag gespeichert")
            st.rerun()

# 🎛️ Tab 2: Daten & Diagramm
with tab2:
    st.header("Daten filtern und visualisieren")

    def dropdown(spalte, label=None):
        label = label or spalte
        return st.selectbox(
            label,
            ["Alle"] + sorted(df[spalte].dropna().astype(str).unique().tolist())
        )

    name_filter = dropdown("Name", "Name auswählen")
    region_filter = dropdown("Körperregion", "Region auswählen")
    medikament_filter = dropdown("Medikament", "Medikament auswählen")
    tageszeit_filter = dropdown("Tageszeit", "Tageszeit auswählen")

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

    # 📊 Diagramm: NRS über Datum
    if not gefiltert.empty and "NRS" in gefiltert.columns and "Zeitpunkt" in gefiltert.columns:
        plot_df = gefiltert.copy()
        plot_df["Datum"] = pd.to_datetime(plot_df["Zeitpunkt"], errors="coerce").dt.date
        plot_df["NRS"] = pd.to_numeric(plot_df["NRS"], errors="coerce")
        plot_df = plot_df.dropna(subset=["Datum", "NRS"])

        if not plot_df.empty:
            plot_df = plot_df.sort_values(by="Datum")
            fig, ax = plt.subplots()
            ax.plot(plot_df["Datum"], plot_df["NRS"], marker="o")
            ax.set_xlabel("Datum")
            ax.set_ylabel("NRS (Schmerzstärke)")
            titel_name = name_filter if name_filter != "Alle" else "Auswahl"
            ax.set_title(f"Schmerzverlauf von {titel_name}")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("Keine gültigen NRS-Daten mit Datum vorhanden.")
    else:
        st.info("Kein NRS-Verlauf darstellbar.")

# 🗂️ Tab 3: Verwaltung
with tab3:
    st.header("Verwaltung")

    if st.button("CSV neu laden"):
        df = pd.read_csv(CSV_DATEI)
        for s in SPALTEN:
            if s not in df.columns:
                df[s] = ""
        df = df[SPALTEN]
        st.success("CSV neu geladen ✅")
        st.dataframe(df)

    if st.button("Alle Daten löschen"):
        df = leeres_df()
        df.to_csv(CSV_DATEI, index=False)
        st.warning("⚠️ Alle Daten gelöscht")
        st.rerun()

    st.download_button(
        label="📥 CSV herunterladen",
        data=open(CSV_DATEI, "rb").read(),
        file_name="schmerzverlauf.csv",
        mime="text/csv"
    )



















