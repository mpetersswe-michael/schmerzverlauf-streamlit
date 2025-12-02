# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from io import BytesIO

# ----------------------------
# Authentifizierung
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    password = st.text_input("Login Passwort", type="password")
    if st.button("Login"):
        if password == "QM1514":
            st.session_state["auth"] = True
            st.success("Login erfolgreich.")
        else:
            st.error("Falsches Passwort.")
    st.stop()

# ----------------------------
# Sidebar mit Logout
# ----------------------------
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state["auth"] = False
        st.stop()

# ----------------------------
# Datenpfade & Initialisierung
# ----------------------------
pain_file = "pain_data.csv"
med_file = "med_data.csv"

# ----------------------------
# Formular: Schmerzverlauf
# ----------------------------
st.markdown("## Schmerzverlauf-Eintrag")
with st.form("pain_form"):
    pain_date = st.date_input("Datum", dt.date.today())
    pain_time = st.time_input("Uhrzeit", dt.datetime.now().time())
    pain_level = st.slider("Schmerzstärke", 0, 10, 5)
    pain_location = st.text_input("Schmerzort")
    pain_note = st.text_area("Bemerkung")
    submitted_pain = st.form_submit_button("Eintrag speichern")

if submitted_pain:
    pain_entry = {
        "Datum": pain_date.strftime("%Y-%m-%d"),
        "Uhrzeit": pain_time.strftime("%H:%M"),
        "Stärke": pain_level,
        "Ort": pain_location,
        "Bemerkung": pain_note
    }
    df_pain = pd.DataFrame([pain_entry])
    try:
        df_existing = pd.read_csv(pain_file)
        df_all = pd.concat([df_existing, df_pain], ignore_index=True)
    except FileNotFoundError:
        df_all = df_pain
    df_all.to_csv(pain_file, index=False)
    st.success("Eintrag gespeichert.")

# ----------------------------
# Formular: Medikamenteneingabe
# ----------------------------
st.markdown("## Medikamenten-Eintrag")
with st.form("med_form"):
    med_date = st.date_input("Medikament-Datum", dt.date.today())
    med_time = st.time_input("Medikament-Uhrzeit", dt.datetime.now().time())
    med_name = st.text_input("Medikament")
    med_dose = st.text_input("Dosierung")
    med_note = st.text_area("Bemerkung")
    submitted_med = st.form_submit_button("Medikament speichern")

if submitted_med:
    med_entry = {
        "Datum": med_date.strftime("%Y-%m-%d"),
        "Uhrzeit": med_time.strftime("%H:%M"),
        "Medikament": med_name,
        "Dosierung": med_dose,
        "Bemerkung": med_note
    }
    df_med = pd.DataFrame([med_entry])
    try:
        df_existing_med = pd.read_csv(med_file)
        df_all_med = pd.concat([df_existing_med, df_med], ignore_index=True)
    except FileNotFoundError:
        df_all_med = df_med
    df_all_med.to_csv(med_file, index=False)
    st.success("Medikament gespeichert.")

# ----------------------------
# Übersichtstabelle
# ----------------------------
st.markdown("## Übersicht Schmerzverlauf")
try:
    df_overview = pd.read_csv(pain_file)
    st.dataframe(df_overview)
except FileNotFoundError:
    st.info("Noch keine Schmerzverlauf-Daten vorhanden.")

# ----------------------------
# Diagramm: Schmerzverlauf
# ----------------------------
st.markdown("## Schmerzverlauf-Diagramm")
try:
    df_plot = pd.read_csv(pain_file)
    df_plot["Zeitstempel"] = pd.to_datetime(df_plot["Datum"] + " " + df_plot["Uhrzeit"])
    df_plot = df_plot.sort_values("Zeitstempel")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df_plot["Zeitstempel"], df_plot["Stärke"], marker="o", color="red")
    ax.set_title("Schmerzverlauf über Zeit")
    ax.set_xlabel("Zeit")
    ax.set_ylabel("Schmerzstärke")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    plt.xticks(rotation=45)
    st.pyplot(fig)
except Exception as e:
    st.warning("Diagramm konnte nicht geladen werden.")






























































