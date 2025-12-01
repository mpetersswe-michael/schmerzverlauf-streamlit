# pain_tracker.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from io import BytesIO

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="Schmerzverlauf", layout="wide")

DATA_FILE_MED = "medications.csv"
DATA_FILE_PAIN = "pain_tracking.csv"

MED_COLUMNS = ["Name", "Datum", "Medikament", "Typ"]
PAIN_COLUMNS = ["Name", "Datum", "Schmerzstärke", "Art", "Lokalisation", "Begleitsymptome", "Bemerkung"]

# ----------------------------
# Hilfsfunktionen
# ----------------------------
def load_data(file, columns):
    try:
        df = pd.read_csv(file, sep=";", encoding="utf-8-sig")
    except:
        df = pd.DataFrame(columns=columns)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    df = df[columns]
    df["Name"] = df["Name"].fillna("").astype(str)
    return df

def filter_by_name_exact(df, name):
    base = df.copy()
    base["Name_clean"] = base["Name"].str.strip().str.lower()
    if name and name.strip():
        mask = base["Name_clean"] == name.strip().lower()
        base = base[mask]
    base = base.drop(columns=["Name_clean"])
    return base

def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def plot_pain(df):
    if df.empty:
        return None
    dfx = df.copy()
    dfx["Datum"] = pd.to_datetime(dfx["Datum"], errors="coerce")
    dfx["Schmerzstärke"] = pd.to_numeric(dfx["Schmerzstärke"], errors="coerce")
    dfx = dfx.dropna(subset=["Datum", "Schmerzstärke"]).sort_values("Datum")
    if dfx.empty:
        return None
    patient_name = dfx["Name"].dropna().unique()
    name_text = patient_name[0].strip() if len(patient_name) > 0 else "Unbekannt"
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    ax.plot(dfx["Datum"], dfx["Schmerzstärke"], color="#b00020", linewidth=2.0, marker="o", markersize=4)
    ax.set_xlabel("Datum", fontsize=11)
    ax.set_ylabel("Schmerzstärke", fontsize=11)
    ax.set_title(f"Schmerzverlauf – {name_text}", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.tick_params(labelsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    return fig

# ----------------------------
# Einfache Authentifizierung
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

st.markdown("<h2>Schmerzverlauf</h2>", unsafe_allow_html=True)
password = st.text_input("Login Passwort", type="password", disabled=st.session_state["auth"])

if not st.session_state["auth"]:
    if password == "QM1514":   # <- hier dein Passwort einsetzen
        st.session_state["auth"] = True
        st.success("Erfolgreich eingeloggt.")
    else:
        st.warning("Bitte Passwort eingeben.")
        st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state.clear()
        st.info("Sie wurden abgemeldet.")
        st.stop()

st.markdown("---")

# ----------------------------
# Daten löschen
# ----------------------------
if st.button("🗑️ Daten löschen"):
    # Medikamente leeren
    pd.DataFrame(columns=MED_COLUMNS).to_csv(DATA_FILE_MED, sep=";", index=False, encoding="utf-8-sig")
    # Schmerzverlauf leeren
    pd.DataFrame(columns=PAIN_COLUMNS).to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")
    st.success("Alle gespeicherten Daten wurden gelöscht.")

# ----------------------------
# Daten anzeigen und exportieren
# ----------------------------
st.markdown("## Daten anzeigen und exportieren")

# Daten laden
df_med_all = load_data(DATA_FILE_MED, MED_COLUMNS)
df_pain_all = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)

# Dropdown-Filter für Medikamente
filter_name_med = st.selectbox(
    "Filter nach Name (Medikamente)",
    options=[""] + sorted(df_med_all["Name"].dropna().str.strip().unique()),
    index=0,
    key="filter_med"
)

# Dropdown-Filter für Schmerzverlauf
filter_name_pain = st.selectbox(
    "Filter nach Name (Schmerzverlauf)",
    options=[""] + sorted(df_pain_all["Name"].dropna().str.strip().unique()),
    index=0,
    key="filter_pain"
)

# Medikamente
st.markdown("### Medikamente")
df_filtered_med = filter_by_name_exact(df_med_all, filter_name_med)
st.dataframe(df_filtered_med, use_container_width=True, height=300)
csv_med = to_csv_semicolon(df_filtered_med)
st.download_button(
    "CSV Medikamente herunterladen",
    data=csv_med,
    file_name=f"medications_{dt.date.today()}.csv",
    mime="text/csv"
)

# Schmerzverlauf
st.markdown("### Schmerzverlauf")
df_filtered_pain = filter_by_name_exact(df_pain_all, filter_name_pain)
st.dataframe(df_filtered_pain, use_container_width=True, height=300)
csv_pain = to_csv_semicolon(df_filtered_pain)
st.download_button(
    "CSV Schmerzverlauf herunterladen",
    data=csv_pain,
    file_name=f"pain_tracking_{dt.date.today()}.csv",
    mime="text/csv"
)

# Diagramm
st.markdown("### Diagramm")
chart_fig = plot_pain(df_filtered_pain)
if chart_fig:
    st.pyplot(chart_fig)
    buf = BytesIO()
    chart_fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    buf.seek(0)
    st.download_button(
        "Diagramm als PNG herunterladen",
        data=buf,
        file_name=f"schmerzverlauf_{dt.date.today()}.png",
        mime="image/png"
    )
else:
    st.info("Keine Daten für das Diagramm vorhanden.")








































