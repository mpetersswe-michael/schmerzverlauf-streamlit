# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from io import BytesIO
import matplotlib.figure
import base64
from pathlib import Path

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="Schmerzverlauf mit linearem Diagramm (etwas größer)", layout="wide")

DATA_FILE_MED = "medications.csv"
DATA_FILE_PAIN = "pain_tracking.csv"

MED_COLUMNS = ["Name", "Datum", "Uhrzeit", "Medikament", "Darreichungsform", "Dosis", "Typ"]
PAIN_COLUMNS = ["Name", "Datum", "Uhrzeit", "Schmerzstärke", "Art", "Lokalisation", "Begleitsymptome", "Bemerkung"]

# ----------------------------
# Styles für Buttons & Login
# ----------------------------
st.markdown("""
    <style>
    /* Button-Design */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        font-size: 1.1em;
        border: none;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
        color: white;
    }

    /* Login-Zeile mit Icon */
    .login-box {
        background-color: #fff8cc;
        padding: 1.4em;
        border-radius: 12px;
        text-align: left;
        margin-bottom: 2em;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 1em;
    }

    .login-icon {
        width: 80px;
        height: auto;
    }

    .login-title {
        font-size: 1.8em;
        font-weight: bold;
        color: saddlebrown;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# Login-Zeile: Icon + Titel nebeneinander
# ----------------------------
st.markdown("""
    <div class="login-box">
        <img src="images-schmerz_icon.png" class="login-icon">
        <div class="login-title">🔒 Login Schmerzverlauf</div>
    </div>
""", unsafe_allow_html=True)

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
    fig, ax = plt.subplots(figsize=(7.5, 4.5))  # etwas größer
    ax.plot(dfx["Datum"], dfx["Schmerzstärke"], color="#b00020", linewidth=2.0, marker="o", markersize=5)
    ax.set_xlabel("Datum", fontsize=11)
    ax.set_ylabel("Schmerzstärke", fontsize=11)
    ax.set_title(f"Schmerzverlauf – {name_text}", fontsize=13)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.tick_params(labelsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    return fig

# ----------------------------
# ----------------------------
# Login-Block
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown('<div class="login-box">🔒 📈 Login Schmerzverlauf</div>', unsafe_allow_html=True)

    password = st.text_input("Login Passwort", type="password", key="login_pw")

    if st.button("Login", key="login_btn"):
        if password == "QM1514":    # ← dein Passwort
            st.session_state["auth"] = True
            st.success("Willkommen – du bist eingeloggt. Bitte bei den drei Punkten oben rechts 'Rerun' starten.")
        else:
            st.error("Falsches Passwort.")
    st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout", key="logout_btn"):
        st.session_state["auth"] = False
        st.stop()

st.markdown("---")

# ----------------------------
# Medikamenten-Eingabe
# ----------------------------
st.markdown("## 💊 Medikamenten-Eintrag")

med_name = st.text_input("Name", key="med_name")
med_date = st.date_input("Datum", value=dt.date.today(), key="med_date")
med_time = st.text_input("Uhrzeit (frei eingeben)", key="med_time")

st.markdown("**Medikament verabreicht?**")
med_given = st.radio("Auswahl", ["Ja", "Nein"], key="med_given")

if med_given == "Ja":
    med_drug = st.text_input("Welches Medikament?", key="med_drug")
    med_form = st.selectbox("Darreichungsform",
                            ["Tablette", "Ampulle s.c.", "Tropfen", "Infusion", "Salbe", "Inhalation"],
                            key="med_form")
    med_dose = st.text_input("Dosis (z. B. 20 mg, 50/4 mg)", key="med_dose")
else:
    med_drug = "keines"
    med_form = ""
    med_dose = ""

med_type = st.selectbox("Typ", ["Dauermedikation", "Bedarfsmedikation"], key="med_type")

if st.button("💾 Medikament speichern", key="med_save_btn"):
    if not med_name.strip():
        st.warning("Bitte einen Namen eingeben.")
    else:
        new_med = pd.DataFrame([{
            "Name": med_name.strip(),
            "Datum": med_date.strftime("%Y-%m-%d"),
            "Uhrzeit": med_time.strip(),
            "Medikament": med_drug.strip(),
            "Darreichungsform": med_form,
            "Dosis": med_dose.strip(),
            "Typ": med_type
        }])
        try:
            existing_med = pd.read_csv(DATA_FILE_MED, sep=";", encoding="utf-8-sig")
        except:
            existing_med = pd.DataFrame(columns=MED_COLUMNS)
        for c in MED_COLUMNS:
            if c not in existing_med.columns:
                existing_med[c] = ""
        existing_med = existing_med[MED_COLUMNS]
        updated_med = pd.concat([existing_med, new_med], ignore_index=True)
        updated_med.to_csv(DATA_FILE_MED, sep=";", index=False, encoding="utf-8-sig")
        st.success("Medikament gespeichert.")

# ----------------------------
# Schmerzverlauf-Eingabe
# ----------------------------
st.markdown("## 📈 Schmerzverlauf-Eintrag")

pain_name = st.text_input("Name", key="pain_name")
pain_date = st.date_input("Datum", value=dt.date.today(), key="pain_date")
pain_time = st.text_input("Uhrzeit (frei eingeben)", key="pain_time")
pain_level = st.slider("Schmerzstärke", 0, 10, 5, key="pain_level")
pain_type = st.text_input("Art", key="pain_type")
pain_location = st.text_input("Lokalisation", key="pain_location")
pain_symptoms = st.text_input("Begleitsymptome", key="pain_symptoms")
pain_note = st.text_area("Bemerkung", key="pain_note")

if st.button("💾 Schmerz-Eintrag speichern", key="pain_save_btn"):
    if not pain_name.strip():
        st.warning("Bitte einen Namen eingeben.")
    else:
        new_pain = pd.DataFrame([{
            "Name": pain_name.strip(),
            "Datum": pain_date.strftime("%Y-%m-%d"),
            "Uhrzeit": pain_time.strip(),
            "Schmerzstärke": pain_level,
            "Art": pain_type.strip(),
            "Lokalisation": pain_location.strip(),
            "Begleitsymptome": pain_symptoms.strip(),
            "Bemerkung": pain_note.strip()
        }])
        try:
            existing_pain = pd.read_csv(DATA_FILE_PAIN, sep=";", encoding="utf-8-sig")
        except:
            existing_pain = pd.DataFrame(columns=PAIN_COLUMNS)
        for c in PAIN_COLUMNS:
            if c not in existing_pain.columns:
                existing_pain[c] = ""

        existing_pain = existing_pain[PAIN_COLUMNS]

        # Anhängen und speichern
        updated_pain = pd.concat([existing_pain, new_pain], ignore_index=True)
        updated_pain.to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")

        st.success("Schmerz-Eintrag gespeichert.", icon="✅")

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

# Medikamente anzeigen
st.markdown("### Medikamente")
df_filtered_med = filter_by_name_exact(df_med_all, filter_name_med)
st.dataframe(df_filtered_med, use_container_width=True, height=300, key="med_table")
csv_med = to_csv_semicolon(df_filtered_med)
st.download_button(
    "CSV Medikamente herunterladen",
    data=csv_med,
    file_name=f"medications_{dt.date.today()}.csv",
    mime="text/csv",
    key="med_csv_dl"
)

# Schmerzverlauf anzeigen
st.markdown("### Schmerzverlauf")
df_filtered_pain = filter_by_name_exact(df_pain_all, filter_name_pain)
st.dataframe(df_filtered_pain, use_container_width=True, height=300, key="pain_table")
csv_pain = to_csv_semicolon(df_filtered_pain)
st.download_button(
    "CSV Schmerzverlauf herunterladen",
    data=csv_pain,
    file_name=f"pain_tracking_{dt.date.today()}.csv",
    mime="text/csv",
    key="pain_csv_dl"
)

# Diagramm
st.markdown("### Diagramm")
chart_fig = plot_pain(df_filtered_pain)

if isinstance(chart_fig, matplotlib.figure.Figure):
    st.pyplot(chart_fig)  # ohne key, stabiler
    buf = BytesIO()
    chart_fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    buf.seek(0)
    st.download_button(
        "Diagramm als PNG herunterladen",
        data=buf,
        file_name=f"schmerzverlauf_{dt.date.today()}.png",
        mime="image/png",
        key="chart_png_dl"
    )
else:
    st.info("Keine gültigen Daten für das Diagramm vorhanden.")

# ----------------------------
# Synchronisation
# ----------------------------
import shutil
import os
import datetime as dt

LOCAL_FILE = "pain_tracking.csv"
SYNC_FOLDER = r"C:\Users\Nutzer\OneDrive\Dokumente\SchmerzverlaufStreamlit"
SYNC_FILENAME = f"pain_tracking_{dt.date.today()}.csv"
SYNC_PATH = os.path.join(SYNC_FOLDER, SYNC_FILENAME)

st.markdown("## 🔄 Synchronisation")

if st.button("Synchronisation starten", key="sync_btn"):
    try:
        if not os.path.exists(SYNC_FOLDER):
            os.makedirs(SYNC_FOLDER)

        if os.path.exists(LOCAL_FILE):
            shutil.copy2(LOCAL_FILE, SYNC_PATH)
            st.success(f"Synchronisation abgeschlossen: Datei gespeichert unter\n`{SYNC_PATH}`")
        else:
            st.error(f"Lokale Datei nicht gefunden: `{LOCAL_FILE}`")
    except Exception as e:
        st.error(f"Fehler bei der Synchronisation: {e}")




































































