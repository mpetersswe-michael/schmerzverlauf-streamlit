import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from io import BytesIO

# ----------------------------
# Button-Styles
# ----------------------------
st.markdown("""
    <style>
    div.stButton > button:nth-of-type(1) {
        background-color: #4CAF50;
        color: white;
    }
    div.stButton > button:nth-of-type(2) {
        background-color: #2196F3;
        color: white;
    }
    div.stButton > button:nth-of-type(3) {
        background-color: #f44336;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="Schmerzverlauf", layout="wide")
st.markdown("# 📈 Schmerzverlauf")

DATA_FILE_MED = "medications.csv"
DATA_FILE_PAIN = "pain_tracking.csv"
MED_COLUMNS = ["Name", "Datum", "Uhrzeit", "Medikament", "Darreichungsform", "Dosis", "Typ"]
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
    return df[columns]

def filter_by_name_exact(df, name):
    df["Name_clean"] = df["Name"].str.strip().str.lower()
    return df[df["Name_clean"] == name.strip().lower()].drop(columns=["Name_clean"]) if name else df.drop(columns=["Name_clean"])

def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def plot_pain(df):
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df["Schmerzstärke"] = pd.to_numeric(df["Schmerzstärke"], errors="coerce")
    df = df.dropna(subset=["Datum", "Schmerzstärke"]).sort_values("Datum")
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    ax.plot(df["Datum"], df["Schmerzstärke"], color="#b00020", linewidth=2.0, marker="o", markersize=4)
    ax.set_title(f"Schmerzverlauf – {df['Name'].iloc[0]}", fontsize=12)
    ax.set_xlabel("Datum"); ax.set_ylabel("Schmerzstärke")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
    fig.autofmt_xdate(rotation=20); fig.tight_layout()
    return fig

# ----------------------------
# Authentifizierung – stabil & vertraut
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

# Login-Bereich
if not st.session_state["auth"]:
    password = st.text_input("Login Passwort", type="password")
    if st.button("Login"):
        if password == "QM1514":  # ← dein Passwort hier
            st.session_state["auth"] = True
            st.experimental_rerun()
        else:
            st.error("Falsches Passwort.")
    st.stop()

# Eingeloggt: App-Inhalte starten
st.success("Du bist eingeloggt.")

# ----------------------------
# Sidebar mit Logout
# ----------------------------
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state["auth"] = False
        st.experimental_rerun()


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

# ----------------------------
# Medikamenten-Eingabe
# ----------------------------
st.markdown("---")
st.markdown("## Medikamenten-Eintrag")

MED_COLUMNS = ["Name", "Datum", "Uhrzeit", "Medikament", "Darreichungsform", "Dosis", "Typ"]

med_name = st.text_input("Name", key="med_name_input")
med_date = st.date_input("Datum", value=dt.date.today(), key="med_date_input")
med_time = st.text_input("Uhrzeit (frei eingeben)", key="med_time_input")

st.markdown("**Medikament verabreicht?**")
med_given = st.radio("Auswahl", ["Ja", "Nein"], key="med_given_input")

if med_given == "Ja":
    med_drug = st.text_input("Welches Medikament?", key="med_drug_input")
    med_form = st.selectbox("Darreichungsform", ["Tablette", "Ampulle s.c.", "Tropfen", "Infusion", "Salbe", "Inhalation"], key="med_form_input")
    med_dose = st.text_input("Dosis (z. B. 20 mg, 50/4 mg)", key="med_dose_input")
else:
    med_drug = "keines"
    med_form = ""
    med_dose = ""

med_type = st.selectbox("Typ", ["Dauermedikation", "Bedarfsmedikation"], key="med_type_input")

if st.button("💾 Medikament speichern"):
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
st.markdown("---")
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

if st.button("💾 Schmerzverlauf speichern"):
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

# ----------------------------
# Diagramm
# ----------------------------
st.markdown("---")
st.markdown("### Diagramm")

# Daten laden und filtern
df_pain_all = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)
filter_name_pain = st.selectbox(
    "Filter nach Name für Diagramm",
    options=[""] + sorted(df_pain_all["Name"].dropna().str.strip().unique()),
    index=0,
    key="filter_pain_chart"
)
df_filtered_pain = filter_by_name_exact(df_pain_all, filter_name_pain)

# Diagramm anzeigen
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


# ----------------------------
# Daten anzeigen und exportieren
# ----------------------------
st.markdown("---")
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
st.dataframe(df_filtered_med, use_container_width=True, height=300)
csv_med = to_csv_semicolon(df_filtered_med)
st.download_button(
    "CSV Medikamente herunterladen",
    data=csv_med,
    file_name=f"medications_{dt.date.today()}.csv",
    mime="text/csv"
)

# Schmerzverlauf anzeigen
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

# ----------------------------
# Datenverwaltung: Löschen mit Passwort
# ----------------------------
st.markdown("---")
st.markdown("## Datenverwaltung")

delete_pw = st.text_input("Passwort für Daten löschen", type="password", key="delete_pw")

if st.button("🗑️ Daten löschen"):
    if delete_pw == "loeschen":  # <- eigenes Passwort für Löschfunktion
        pd.DataFrame(columns=MED_COLUMNS).to_csv(DATA_FILE_MED, sep=";", index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=PAIN_COLUMNS).to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")
        st.success("Alle gespeicherten Daten wurden gelöscht.")
    else:
        st.error("Falsches Passwort – Daten wurden nicht gelöscht.")




















































