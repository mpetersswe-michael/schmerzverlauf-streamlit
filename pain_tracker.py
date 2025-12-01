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
# Hilfsfunktionen
# ----------------------------
def load_data(file, columns):
    try:
        df = pd.read_csv(file)
        return df[columns]
    except Exception:
        return pd.DataFrame(columns=columns)

def filter_by_name(df, name):
    if name:
        return df[df["Name"].str.contains(name, case=False, na=False)]
    return df

def plot_pain(df):
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(6, 3))  # größer, klare Schrift
    ax.plot(df["Datum"], df["Schmerzstärke"], marker="o", color="steelblue")
    ax.set_xlabel("Datum", fontsize=10, fontweight="normal")
    ax.set_ylabel("Schmerzstärke", fontsize=10, fontweight="normal")
    ax.set_title("Schmerzverlauf", fontsize=12, fontweight="normal")
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    return fig

# ----------------------------
# Login
# ----------------------------
st.title("Schmerzverlauf")

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
    st.info("Hier könnten Eingabefelder für neue Daten stehen.")

# ----------------------------
# Tab 2: Medikamente
# ----------------------------
with tab2:
    st.subheader("Medikamentenliste")

    filter_name = st.text_input("Filter nach Name (optional)", value="")

    df_med = load_data(DATA_FILE_MED, MED_COLUMNS)
    df_filtered_med = filter_by_name(df_med, filter_name)

    # Überschrift mit Patientennamen
    if filter_name:
        st.markdown(f"### Medikamentenliste für Patient: {filter_name}")
    else:
        st.markdown("### Medikamentenliste")

    # Tabelle mit hoher Header-Zeile
    st.dataframe(df_filtered_med, use_container_width=True, height=300)

    # CSV-Export
    csv_med = df_filtered_med[MED_COLUMNS].to_csv(index=False, encoding="utf-8")
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

    filter_name = st.text_input("Filter nach Name (optional)", value="", key="pain_filter")

    df_pain = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)
    df_filtered_pain = filter_by_name(df_pain, filter_name)

    st.dataframe(df_filtered_pain, use_container_width=True, height=400)

    # CSV-Export
    csv_pain = df_filtered_pain[PAIN_COLUMNS].to_csv(index=False, encoding="utf-8")
    st.download_button(
        "CSV Schmerzverlauf herunterladen",
        data=csv_pain,
        file_name=f"pain_tracking_{dt.date.today()}.csv",
        mime="text/csv"
    )

    # Diagramm größer, klare Schrift
    chart_fig = plot_pain(df_filtered_pain)
    if chart_fig:
        st.pyplot(chart_fig)





