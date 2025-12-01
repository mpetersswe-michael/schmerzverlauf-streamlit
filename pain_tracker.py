# pain_tracker.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from io import BytesIO

st.markdown("""
    <style>
    div.stButton > button:nth-child(1) {
        background-color: #4CAF50; /* Grün */
        color: white;
    }
    div.stButton > button:nth-child(2) {
        background-color: #2196F3; /* Blau */
        color: white;
    }
    div.stButton > button:nth-child(3) {
        background-color: #f44336; /* Rot */
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)


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
    if name and str(name).strip():
        mask = base["Name_clean"] == str(name).strip().lower()
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
# Authentifizierung
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

st.markdown("<h2>Schmerzverlauf</h2>", unsafe_allow_html=True)
password = st.text_input("Login Passwort", type="password", disabled=st.session_state["auth"])

if not st.session_state["auth"]:
    if password == "geheim":
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
# Formular-Reset
# ----------------------------
if st.button("✏️ Neuer Eintrag"):
    st.session_state["med_name"] = ""
    st.session_state["med_date"] = dt.date.today()
    st.session_state["med_given"] = "Nein"
    st.session_state["med_drug"] = ""
    st.session_state["med_type"] = "Dauermedikation"
    st.session_state["pain_name"] = ""
    st.session_state["pain_date"] = dt.date.today()
    st.session_state["pain_level"] = 0
    st.session_state["pain_notes"] = ""
    for label in ["Stechend", "Dumpf", "Brennend", "Ziehend"]:
        st.session_state[f"type_{label}"] = False
    for label in ["Kopf", "Rücken", "Bauch", "Bein"]:
        st.session_state[f"loc_{label}"] = False
    for label in ["Übelkeit", "Erbrechen"]:
        st.session_state[f"sym_{label}"] = False
    st.success("Formulare zurückgesetzt.")

st.markdown("---")

# ----------------------------
# Medikamenten-Eingabe
# ----------------------------
st.markdown("## Medikamenten-Eintrag")

med_name = st.text_input("Name", key="med_name", value=st.session_state.get("med_name", ""))
med_date = st.date_input("Datum", value=st.session_state.get("med_date", dt.date.today()), key="med_date")

st.markdown("**Medikament verabreicht?**")
med_given = st.radio("Auswahl", ["Ja", "Nein"], key="med_given", index=0 if st.session_state.get("med_given") == "Ja" else 1)

if med_given == "Ja":
    med_drug = st.text_input("Welches Medikament?", key="med_drug", value=st.session_state.get("med_drug", ""))
else:
    med_drug = "keines"

med_type = st.selectbox("Typ", ["Dauermedikation", "Bedarfsmedikation"], key="med_type")

if st.button("💾 Medikament speichern", key="med_save"):
    if not med_name.strip():
        st.warning("Bitte einen Namen eingeben.")
    else:
        new_med = pd.DataFrame([{
            "Name": med_name.strip(),
            "Datum": med_date.strftime("%Y-%m-%d"),
            "Medikament": med_drug.strip(),
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

st.markdown("---")

# ----------------------------
# Schmerzverlauf-Eingabe
# ----------------------------
st.markdown("## Schmerzverlauf-Eintrag")

pain_name = st.text_input("Name", key="pain_name", value=st.session_state.get("pain_name", ""))
pain_date = st.date_input("Datum", value=st.session_state.get("pain_date", dt.date.today()), key="pain_date")
pain_level = st.slider("Schmerzstärke (NRS 0–10)", min_value=0, max_value=10, step=1, key="pain_level")

st.markdown("**Art**")
pain_types = []
for label in ["Stechend", "Dumpf", "Brennend", "Ziehend"]:
    if st.checkbox(label, key=f"type_{label}", value=st.session_state.get(f"type_{label}", False)):
        pain_types.append(label)

st.markdown("**Lokalisation**")
pain_locations = []
for label in ["Kopf", "Rücken", "Bauch", "Bein"]:
    if st.checkbox(label, key=f"loc_{label}", value=st.session_state.get(f"loc_{label}", False)):
        pain_locations.append(label)

st.markdown("**Begleitsymptome**")
pain_symptoms = []
for label in ["Übelkeit", "Erbrechen"]:
    if st.checkbox(label, key=f"sym_{label}", value=st.session_state.get(f"sym_{label}", False)):
        pain_symptoms.append(label)

pain_notes = st.text_area("Bemerkungen", key="pain_notes", value=st.session_state.get("pain_notes", ""))

if st.button("💾 Schmerzverlauf speichern", key="pain_save"):
    if not pain_name.strip():
        st.warning("Bitte einen Namen eingeben.")
    else:
        new_pain = pd.DataFrame([{
            "Name": pain_name.strip(),
            "Datum": pain_date.strftime("%Y-%m-%d"),
            "Schmerzstärke": pain_level,
            "Art": ", ".join(pain_types),
            "Lokalisation": ", ".join(pain_locations),
            "Begleitsymptome": ", ".join(pain_symptoms),
            "Bemerkung": pain_notes.strip()
        }])
        try:
            existing_pain = pd.read_csv(DATA_FILE_PAIN, sep=";", encoding="utf-8-sig")
        except:
            existing_pain = pd.DataFrame(columns=PAIN_COLUMNS)
        for c in PAIN_COLUMNS:
            if c not in existing_pain.columns:
                existing_pain[c] = ""
        existing_pain = existing_pain[PAIN_COLUMNS]
        updated_pain = pd.concat([existing_pain, new_pain], ignore_index=True)
        updated_pain.to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")
        st.success("Schmerzverlauf gespeichert.")

st.markdown("---")

# ----------------------------
# Datenverwaltung: Löschen mit Passwort
# ----------------------------
st.markdown("## Datenverwaltung")
delete_pw = st.text_input("Passwort für Daten löschen", type="password", key="delete_pw")
if st.button("🗑️ Daten löschen", key="delete_data"):
    if delete_pw == "loeschen":  # <- eigenes Passwort für Löschfunktion
        pd.DataFrame(columns=MED_COLUMNS).to_csv(DATA_FILE_MED, sep=";", index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=PAIN_COLUMNS).to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")
        st.success("Alle gespeicherten Daten wurden gelöscht.")
    else:
        st.error("Falsches Passwort – Daten wurden nicht gelöscht.")

st.markdown("---")

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














































