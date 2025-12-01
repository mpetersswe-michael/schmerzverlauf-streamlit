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
    """CSV laden; fehlende Spalten ergänzen; robuste Rückgabe."""
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
    # Namen bereinigen: trimmen + lowercase
    base["Name_clean"] = base["Name"].str.strip().str.lower()
    if name and name.strip():
        mask = base["Name_clean"] == name.strip().lower()
        base = base[mask]
    base = base.drop(columns=["Name_clean"])
    return base

def to_csv_semicolon(df):
    """CSV mit Semikolon als Separator und UTF-8-SIG-Encoding."""
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def plot_pain(df):
    """Kleines Liniendiagramm für Schmerzverlauf mit deutschem Datumsformat."""
    if df.empty:
        return None
    dfx = df.copy()
    dfx["Datum"] = pd.to_datetime(dfx["Datum"], errors="coerce")
    dfx["Schmerzstärke"] = pd.to_numeric(dfx["Schmerzstärke"], errors="coerce")
    dfx = dfx.dropna(subset=["Datum", "Schmerzstärke"]).sort_values("Datum")
    if dfx.empty:
        return None
    patient_name = dfx["Name"].dropna().unique()
    name_text = patient_name[0].strip() if len(patient_name) > 0 and isinstance(patient_name[0], str) and patient_name[0].strip() else "Unbekannt"
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
# Formular-Reset ("Neuer Eintrag")
# ----------------------------
if st.button("✏️ Neuer Eintrag"):
    for key in ["med_name", "med_drug", "pain_name", "pain_notes"]:
        st.session_state[key] = ""
    st.session_state["med_type"] = "Dauermedikation"
    st.session_state["med_date"] = dt.date.today()
    st.session_state["pain_date"] = dt.date.today()
    st.session_state["pain_level"] = 0
    # Checkbox-Reset sicherheitshalber
    for label in ["Stechend", "Dumpf", "Brennend", "Ziehend", "Kopf", "Rücken", "Bauch", "Bein", "Übelkeit", "Erbrechen"]:
        for prefix in ["type_", "loc_", "sym_"]:
            k = f"{prefix}{label}"
            if k in st.session_state:
                st.session_state[k] = False

# ----------------------------
# Medikamenten-Eingabe
# ----------------------------
st.markdown("## Medikamenten-Eintrag")
med_name = st.text_input("Name", key="med_name")
med_date = st.date_input("Datum", value=st.session_state.get("med_date", dt.date.today()), key="med_date")
med_drug = st.text_input("Medikament", key="med_drug")
med_type = st.selectbox("Typ", ["Dauermedikation", "Bedarfsmedikation"], key="med_type")

if st.button("Medikament speichern"):
    if not med_name.strip():
        st.warning("Bitte einen Namen eingeben.")
    elif not med_drug.strip():
        st.warning("Bitte ein Medikament eingeben.")
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
        updated_med = pd.concat([existing_med, new_med], ignore_index=True)
        updated_med.to_csv(DATA_FILE_MED, sep=";", index=False, encoding="utf-8-sig")
        st.success("Medikament gespeichert.")

# ----------------------------
# Schmerzverlauf-Eingabe
# ----------------------------
st.markdown("## Schmerzverlauf-Eintrag")
pain_name = st.text_input("Name", key="pain_name")
pain_date = st.date_input("Datum", value=st.session_state.get("pain_date", dt.date.today()), key="pain_date")
pain_level = st.slider("Schmerzstärke (NRS 0–10)", min_value=0, max_value=10, step=1, key="pain_level")

st.markdown("**Art**")
pain_types = [label for label in ["Stechend", "Dumpf", "Brennend", "Ziehend"] if st.checkbox(label, key=f"type_{label}")]

st.markdown("**Lokalisation**")
pain_locations = [label for label in ["Kopf", "Rücken", "Bauch", "Bein"] if st.checkbox(label, key=f"loc_{label}")]

st.markdown("**Begleitsymptome**")
pain_symptoms = [label for label in ["Übelkeit", "Erbrechen"] if st.checkbox(label, key=f"sym_{label}")]

pain_notes = st.text_area("Bemerkungen", key="pain_notes")

if st.button("Schmerzverlauf speichern"):
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
        updated_pain = pd.concat([existing_pain, new_pain], ignore_index=True)
        updated_pain.to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")
        st.success("Schmerzverlauf gespeichert.")

# ----------------------------
# Daten anzeigen und exportieren
# ----------------------------
st.markdown("## Daten anzeigen und exportieren")

# Daten laden
df_med_all = load_data(DATA_FILE_MED, MED_COLUMNS)
df_pain_all = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)

# Gemeinsames Filterfeld für beide Tabellen
filter_name = st.text_input("Filter nach Name (exakt)", value="", key="filter_all")

# Medikamente
st.markdown("### Medikamente")
df_filtered_med = filter_by_name_exact(df_med_all, filter_name)
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
df_filtered_pain = filter_by_name_exact(df_pain_all, filter_name)
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



































