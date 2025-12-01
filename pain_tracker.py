import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

# ----------------------------
# Konfiguration
# ----------------------------
st.set_page_config(page_title="Schmerzverlauf", layout="wide")

DATA_FILE_MED = "medications.csv"
DATA_FILE_PAIN = "pain_tracking.csv"

MED_COLUMNS = ["Name", "Datum", "Medikament"]
PAIN_COLUMNS = ["Name", "Datum", "Schmerzstärke"]

# ----------------------------
# Globales CSS (höhere Tabellen-Headerzeilen)
# ----------------------------
st.markdown(
    """
    <style>
    /* Tabellenkopf optisch höher durch Padding (ca. 25px) */
    thead tr th {
        padding-top: 12px !important;
        padding-bottom: 12px !important;
        font-weight: 400 !important;
    }
    /* Normale Schrift in Tabellenzellen */
    tbody tr td {
        font-weight: 400 !important;
    }
    /* Kleines rotes Diagramm-Icon neben Überschriften */
    .red-chart-icon {
        display: inline-block;
        width: 14px;
        height: 14px;
        margin-right: 8px;
        background: linear-gradient(135deg, #b00020 0%, #ff3b30 100%);
        clip-path: polygon(0% 70%, 20% 60%, 35% 75%, 55% 40%, 70% 55%, 85% 30%, 100% 45%, 100% 100%, 0% 100%);
        vertical-align: middle;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Hilfsfunktionen
# ----------------------------
def load_data(file: str, columns: list[str]) -> pd.DataFrame:
    try:
        df = pd.read_csv(file, sep=";", encoding="utf-8-sig")
        # Nur gewünschte Spalten, fehlende ggf. ergänzen
        for c in columns:
            if c not in df.columns:
                df[c] = ""  # leere Spalte sicherstellen
        return df[columns]
    except Exception:
        return pd.DataFrame(columns=columns)

def filter_by_name(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if name:
        return df[df["Name"].str.contains(name, case=False, na=False)]
    return df

def to_csv_semicolon(df: pd.DataFrame) -> bytes:
    # Semikolon als Trennzeichen + UTF-8 mit BOM → Excel trennt korrekt in Spalten
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def plot_pain(df: pd.DataFrame):
    if df.empty:
        return None
    # Datum sicher parsen und sortieren
    dfx = df.copy()
    dfx["Datum"] = pd.to_datetime(dfx["Datum"], errors="coerce")
    dfx = dfx.dropna(subset=["Datum"]).sort_values("Datum")

    fig, ax = plt.subplots(figsize=(7, 3.5))  # größer, klar
    ax.plot(
        dfx["Datum"],
        dfx["Schmerzstärke"],
        color="#b00020",           # roter Verlauf
        linewidth=2.0,
        marker="o",
        markersize=4
    )
    ax.set_xlabel("Datum", fontsize=11)
    ax.set_ylabel("Schmerzstärke", fontsize=11)
    ax.set_title("Schmerzverlauf", fontsize=12)  # kein Fettdruck (Standard)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.tick_params(labelsize=10)
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    return fig

# ----------------------------
# Startseite mit Login
# ----------------------------
st.markdown("<span class='red-chart-icon'></span><span style='font-size:28px;'>Schmerzverlauf</span>", unsafe_allow_html=True)

password = st.text_input("Login Passwort", type="password")
if password != "geheim":   # Beispiel-Passwort
    st.warning("Bitte Passwort eingeben")
    st.stop()

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3 = st.tabs(["Eintrag", "Medikamente", "Verlauf"])

# ----------------------------
# Tab 1: Eintrag
# ----------------------------
with tab1:
    st.subheader("Neuen Eintrag hinzufügen")
    st.info("Hier können später Eingabefelder für neue Daten stehen.")

# ----------------------------
# Tab 2: Medikamente
# ----------------------------
with tab2:
    st.subheader("Medikamentenliste")

    filter_name_med = st.text_input("Filter nach Name (optional)", value="", key="med_filter")

    df_med = load_data(DATA_FILE_MED, MED_COLUMNS)
    df_filtered_med = filter_by_name(df_med, filter_name_med)

    # Überschrift mit Patientennamen (falls gesetzt)
    if filter_name_med.strip():
        st.markdown(f"### Medikamentenliste für Patient: {filter_name_med}")
    else:
        st.markdown("### Medikamentenliste")

    st.dataframe(df_filtered_med, use_container_width=True, height=320)

    # CSV-Export (Semikolon, UTF-8 BOM) → Excel trennt korrekt
    csv_med = to_csv_semicolon(df_filtered_med[MED_COLUMNS])
    st.download_button(
        "CSV Medikamente herunterladen",
        data=csv_med,
        file_name=f"medications_{dt.date.today()}.csv",
        mime="text/csv"
    )

# ----------------------------
# Tab 3: Verlauf
# ----------------------------
with tab3:
    st.subheader("Schmerzverlauf")

    filter_name_pain = st.text_input("Filter nach Name (optional)", value="", key="pain_filter")

    df_pain = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)
    df_filtered_pain = filter_by_name(df_pain, filter_name_pain)

    st.dataframe(df_filtered_pain, use_container_width=True, height=380)

    # CSV-Export (Semikolon, UTF-8 BOM)
    csv_pain = to_csv_semicolon(df_filtered_pain[PAIN_COLUMNS])
    st.download_button(
        "CSV Schmerzverlauf herunterladen",
        data=csv_pain,
        file_name=f"pain_tracking_{dt.date.today()}.csv",
        mime="text/csv"
    )

    # Diagramm sichtbar, größer, klare Schrift, kein Fettdruck
    chart_fig = plot_pain(df_filtered_pain)
    if chart_fig:
        st.pyplot(chart_fig)
    else:
        st.info("Keine Daten für das Diagramm vorhanden.")







