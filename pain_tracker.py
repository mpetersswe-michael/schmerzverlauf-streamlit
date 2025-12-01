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

MED_COLUMNS = ["Name", "Datum", "Medikament", "Typ"]
PAIN_COLUMNS = ["Name", "Datum", "Schmerzstärke", "Art", "Lokalisation", "Begleitsymptome", "Bemerkung"]

# ----------------------------
# CSS
# ----------------------------
st.markdown("""
<style>
thead tr th {
    padding-top: 12px !important;
    padding-bottom: 12px !important;
    font-weight: 400 !important;
}
tbody tr td {
    font-weight: 400 !important;
}
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
""", unsafe_allow_html=True)

# ----------------------------
# Hilfsfunktionen
# ----------------------------
def load_data(file, columns):
    try:
        df = pd.read_csv(file, sep=";", encoding="utf-8-sig")
        for c in columns:
            if c not in df.columns:
                df[c] = ""
        return df[columns]
    except:
        return pd.DataFrame(columns=columns)

def filter_by_name(df, name):
    if name:
        return df[df["Name"].str.contains(name, case=False, na=False)]
    return df

def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def plot_pain(df):
    if df.empty:
        return None
    dfx = df.copy()
    dfx["Datum"] = pd.to_datetime(dfx["Datum"], errors="coerce")
    dfx = dfx.dropna(subset=["Datum"]).sort_values("Datum")
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(dfx["Datum"], dfx["Schmerzstärke"], color="#b00020", linewidth=2.0, marker="o", markersize=4)
    ax.set_xlabel("Datum", fontsize=11)
    ax.set_ylabel("Schmerzstärke", fontsize=11)
    ax.set_title("Schmerzverlauf", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.tick_params(labelsize=10)
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    return fig

# ----------------------------
# Login
# ----------------------------
st.markdown("<span class='red-chart-icon'></span><span style='font-size:28px;'>Schmerzverlauf</span>", unsafe_allow_html=True)
password = st.text_input("Login Passwort", type="password")
if password != "geheim":
    st.warning("Bitte Passwort eingeben")
    st.stop()

# ----------------------------
# Sidebar mit Logout
# ----------------------------
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state.clear()
        st.info("Sie wurden abgemeldet.")
        st.stop()
# ----------------------------
# Schmerzverlauf-Eintrag
# ----------------------------
st.markdown("## Schmerzverlauf-Eintrag")
pain_name = st.text_input("Name", key="pain_name")
pain_date = st.date_input("Datum", value=dt.date.today(), key="pain_date")
pain_level = st.slider("Schmerzstärke (0–10)", min_value=0, max_value=10, key="pain_level")

# Schmerzart
st.markdown("**Art**")
pain_types = []
for label in ["Stechend", "Dumpf", "Brennend", "Ziehend"]:
    if st.checkbox(label, key=f"type_{label}"):
        pain_types.append(label)

# Lokalisation
st.markdown("**Lokalisation**")
pain_locations = []
for label in ["Kopf", "Rücken", "Bauch", "Bein"]:
    if st.checkbox(label, key=f"loc_{label}"):
        pain_locations.append(label)

# Begleitsymptome
st.markdown("**Begleitsymptome**")
pain_symptoms = []
for label in ["Übelkeit", "Erbrechen"]:
    if st.checkbox(label, key=f"sym_{label}"):
        pain_symptoms.append(label)

# Bemerkung
pain_notes = st.text_area("Bemerkungen", key="pain_notes")

# Speichern
if st.button("Schmerzverlauf speichern"):
    new_pain = pd.DataFrame([{
        "Name": pain_name,
        "Datum": pain_date.strftime("%Y-%m-%d"),
        "Schmerzstärke": pain_level,
        "Art": ", ".join(pain_types),
        "Lokalisation": ", ".join(pain_locations),
        "Begleitsymptome": ", ".join(pain_symptoms),
        "Bemerkung": pain_notes
    }])
    try:
        existing_pain = pd.read_csv(DATA_FILE_PAIN, sep=";", encoding="utf-8-sig")
    except:
        existing_pain = pd.DataFrame(columns=PAIN_COLUMNS)
    updated_pain = pd.concat([existing_pain, new_pain], ignore_index=True)
    updated_pain.to_csv(DATA_FILE_PAIN, sep=";", index=False, encoding="utf-8-sig")
    st.success("Schmerzverlauf gespeichert.")

# Medikamenten-Eintrag
# ----------------------------
st.markdown("## Medikamenten-Eintrag")
med_name = st.text_input("Name", key="med_name")
med_date = st.date_input("Datum", value=dt.date.today(), key="med_date")
med_drug = st.text_input("Medikament", key="med_drug")
med_type = st.selectbox("Typ", ["Dauermedikation", "Bedarfsmedikation"], key="med_type")

if st.button("Medikament speichern"):
    new_med = pd.DataFrame([{
        "Name": med_name,
        "Datum": med_date.strftime("%Y-%m-%d"),
        "Medikament": med_drug,
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
# Daten anzeigen und exportieren
# ----------------------------
st.markdown("## Daten anzeigen und exportieren")
filter_name = st.text_input("Filter nach Name (optional)", value="", key="filter_all")

# Medikamente
st.markdown("### Medikamentenliste")
df_med = load_data(DATA_FILE_MED, MED_COLUMNS)
df_filtered_med = filter_by_name(df_med, filter_name)
st.dataframe(df_filtered_med, use_container_width=True, height=300)
csv_med = to_csv_semicolon(df_filtered_med)
st.download_button("CSV Medikamente herunterladen", data=csv_med, file_name=f"medications_{dt.date.today()}.csv", mime="text/csv")

# Schmerzverlauf
st.markdown("### Schmerzverlauf")
df_pain = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)
df_filtered_pain = filter_by_name(df_pain, filter_name)
st.dataframe(df_filtered_pain, use_container_width=True, height=300)
csv_pain = to_csv_semicolon(df_filtered_pain)
st.download_button("CSV Schmerzverlauf herunterladen", data=csv_pain, file_name=f"pain_tracking_{dt.date.today()}.csv", mime="text/csv")

# Diagramm
st.markdown("### Diagramm")
chart_fig = plot_pain(df_filtered_pain)
if chart_fig:
    st.pyplot(chart_fig)
else:
    st.info("Keine Daten für das Diagramm vorhanden.")






