import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dateutil import parser
import os

st.set_page_config(page_title="Schmerzverlauf", layout="centered")

# Passwortschutz
try:
    PASSWORT = st.secrets["app_password"]
except Exception:
    st.error("⚠️ Kein Passwort in st.secrets gesetzt.")
    st.stop()

if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False

# CSV-Dateien
CSV_DATEI = "schmerzverlauf.csv"
BACKUP_DATEI = "schmerzverlauf_backup.csv"

# Feste Spaltenreihenfolge (Legacy, vollständig)
SPALTEN = [
    "Name",
    "Körperregion",
    "Schmerzempfinden",
    "NRS",
    "Tageszeit",
    "Medikament",
    "Dosierung",
    "Zeitpunkt",
    "Notizen"
]

def leeres_df():
    return pd.DataFrame(columns=SPALTEN)

def normiere_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Fehlende Spalten hinzufügen
    for s in SPALTEN:
        if s not in df_raw.columns:
            df_raw[s] = ""
    # Nur erwartete Spalten und richtige Reihenfolge
    df = df_raw[SPALTEN].copy()

    # Typen/Strings normalisieren: Tabs raus, trimmen
    for s in SPALTEN:
        df[s] = df[s].astype(str).str.replace("\t", " ").str.strip()
        # Leerstring statt "nan"
        df[s] = df[s].replace({"nan": ""})

    # NRS als Zahl
    df["NRS"] = pd.to_numeric(df["NRS"], errors="coerce")

    # Zeitpunkt bleibt String; Parsing erfolgt erst fürs Plot
    df["Zeitpunkt"] = df["Zeitpunkt"].astype(str)

    return df

def lade_csv(pfad: str) -> pd.DataFrame:
    if os.path.exists(pfad):
        df_loaded = pd.read_csv(pfad, sep=";", encoding="utf-8")
        return normiere_dataframe(df_loaded)
    else:
        df_empty = leeres_df()
        df_empty.to_csv(pfad, index=False, sep=";", encoding="utf-8")
        return df_empty

# Laden oder neu erstellen + Backup
try:
    df = lade_csv(CSV_DATEI)
    st.success(f"✅ {len(df)} Einträge geladen.")
    df.to_csv(BACKUP_DATEI, index=False, sep=";", encoding="utf-8")
    st.info("📂 Backup gespeichert als 'schmerzverlauf_backup.csv'")
except Exception as e:
    st.error(f"❌ Fehler beim Laden: {e}")
    df = leeres_df()

# Sidebar Login
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

# Tabs
tab1, tab2, tab3 = st.tabs(["Eingabe", "Daten & Diagramm", "Verwaltung"])

# Tab 1: Eingabe
with tab1:
    st.header("Schmerzverlauf erfassen")

    with st.form("eingabe_formular", clear_on_submit=True):
        name = st.text_input("Name (Patient)")
        koerperregion = st.text_input("Körperregion")
        schmerzempfinden = st.text_input("Schmerzempfinden")
        nrs = st.number_input("NRS (0–10)", min_value=0, max_value=10, step=1)
        tageszeit = st.text_input("Tageszeit")
        medikament = st.text_input("Medikament")
        dosierung = st.text_input("Dosierung (z. B. 400)")
        zeitpunkt = st.text_input("Zeitpunkt (z. B. 30.11.25, 30.11.2025 oder 2025-11-30)")
        notizen = st.text_area("Notizen (frei)")

        submitted = st.form_submit_button("➕ Eintrag speichern")
        if submitted:
            neuer_eintrag = pd.DataFrame([{
                "Name": name,
                "Körperregion": koerperregion,
                "Schmerzempfinden": schmerzempfinden,
                "NRS": nrs,
                "Tageszeit": tageszeit,
                "Medikament": medikament,
                "Dosierung": dosierung,
                "Zeitpunkt": zeitpunkt,
                "Notizen": notizen
            }])
            neuer_eintrag = normiere_dataframe(neuer_eintrag)
            df = pd.concat([df, neuer_eintrag], ignore_index=True)
            df.to_csv(CSV_DATEI, index=False, sep=";", encoding="utf-8")
            st.success("✅ Eintrag gespeichert")
            st.rerun()

# Tab 2: Daten & Diagramm
with tab2:
    st.header("Daten filtern und visualisieren")

    def dropdown(spalte, label=None):
        label = label or spalte
        werte = df[spalte].dropna().astype(str).unique().tolist()
        werte = [w for w in werte if w.strip() != ""]
        return st.selectbox(label, ["Alle"] + sorted(werte))

    name_filter = dropdown("Name", "Name auswählen")
    region_filter = dropdown("Körperregion", "Körperregion auswählen")
    tageszeit_filter = dropdown("Tageszeit", "Tageszeit auswählen")
    medikament_filter = dropdown("Medikament", "Medikament auswählen")

    gefiltert = df.copy()
    if name_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Name"] == name_filter]
    if region_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Körperregion"] == region_filter]
    if tageszeit_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Tageszeit"] == tageszeit_filter]
    if medikament_filter != "Alle":
        gefiltert = gefiltert[gefiltert["Medikament"] == medikament_filter]

    st.dataframe(gefiltert)

    # Flexible Datumserkennung
    def parse_datum(s):
        try:
            return parser.parse(s, dayfirst=True).date()
        except Exception:
            return None

    # Diagramm: NRS über Datum (Linie verbindet alle Punkte)
    if not gefiltert.empty:
        plot_df = gefiltert.copy()
        plot_df["NRS"] = pd.to_numeric(plot_df["NRS"], errors="coerce")
        plot_df["Datum"] = plot_df["Zeitpunkt"].apply(parse_datum)
        plot_df = plot_df.dropna(subset=["NRS", "Datum"])

        if not plot_df.empty:
            plot_df = plot_df.sort_values(by="Datum")
            plot_df["Datum_fmt"] = plot_df["Datum"].apply(lambda d: d.strftime("%d.%m.%y"))

            fig, ax = plt.subplots()
            ax.plot(plot_df["Datum_fmt"], plot_df["NRS"], marker="o", linestyle="-")  # Linie sichtbar
            ax.set_xlabel("Datum")
            ax.set_ylabel("NRS (Schmerzstärke)")
            ax.set_ylim(0, 10)
            titel_name = name_filter if name_filter != "Alle" else "Auswahl"
            ax.set_title(f"Schmerzverlauf von {titel_name}")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("Keine gültigen NRS-Daten mit Datum vorhanden.")
    else:
        st.info("Keine Daten für die gewählte Filterkombination.")

# Tab 3: Verwaltung
with tab3:
    st.header("Verwaltung")

    if st.button("CSV neu laden"):
        try:
            df = lade_csv(CSV_DATEI)
            st.success("CSV neu geladen ✅")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Fehler beim Neuladen: {e}")

    if st.button("Alle Daten löschen"):
        df = leeres_df()
        df.to_csv(CSV_DATEI, index=False, sep=";", encoding="utf-8")
        st.warning("⚠️ Alle Daten gelöscht")
        st.rerun()

    # Download spiegelt exakt die aktuelle Datei (UTF-8, ;)
    st.download_button(
        label="📥 CSV herunterladen",
        data=open(CSV_DATEI, "rb").read(),
        file_name="schmerzverlauf.csv",
        mime="text/csv"
    )





























