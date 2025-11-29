import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import os

st.set_page_config(page_title="Schmerzverlauf", layout="centered")

st.title("🩺 Schmerzverlauf erfassen und visualisieren")

# Eingabefelder
patient_name = st.text_input("Name (Patient)")
region = st.selectbox("Körperregion", ["Kopf", "Rücken", "Bein", "Arm", "Bauch"])
pain_type = st.radio("Schmerzempfinden", ["Stechend", "Dumpf", "Brennend", "Ziehend"])
intensity = st.slider("NRS (0-10)", 0, 10, 5)
medication_name = st.text_input("Medikament")
dosage = st.text_input("Dosierung")
medication_unit = st.selectbox("Einheit", ["mg", "Tablette", "Ampulle", "Tropfen"])
before_after = st.radio("Zeitpunkt", ["Vor Schmerzmittel-Einnahme", "Nach Schmerzmittel-Einnahme"])
notes = st.text_area("Begleitsymptome / Notizen")
tageszeit = st.selectbox("Tageszeit", ["Morgen", "Mittag", "Abend", "Nacht"])

# Dry-run Option
dry_run = st.checkbox("Dry-run Modus aktivieren (keine Speicherung)")

# CSV-Datei
CSV_FILE = "pain_log.csv"
expected_columns = ["Datum", "Uhrzeit", "Name", "Region", "Schmerzempfinden",
                    "NRS", "Medikament", "Dosierung", "Einheit",
                    "Vor/Nach Einnahme", "Tageszeit", "Begleitsymptome"]

def initialize_csv():
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(expected_columns)
    st.warning("⚠️ Die CSV-Datei war unvollständig oder beschädigt und wurde neu initialisiert.")

def save_entry():
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(expected_columns)
        writer.writerow([
            datetime.now().date(),
            datetime.now().time().strftime("%H:%M:%S"),
            patient_name, region, pain_type, intensity,
            medication_name, dosage, medication_unit,
            before_after, tageszeit, notes
        ])

if st.button("Speichern"):
    if dry_run:
        st.info("Dry-run aktiv: Daten wurden nicht gespeichert.")
    else:
        save_entry()
        st.success("Eintrag gespeichert!")

# CSV laden und prüfen
if os.path.isfile(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            initialize_csv()
            df = pd.read_csv(CSV_FILE)
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der CSV-Datei: {e}")
        initialize_csv()
        df = pd.read_csv(CSV_FILE)

    st.subheader("📋 Gespeicherte Einträge")
    st.dataframe(df)

    # Filtersektion
    st.subheader("🔎 Filter")
    filter_patient = st.multiselect("Filter nach Patient", df["Name"].unique())
    filter_med = st.multiselect("Filter nach Medikament", df["Medikament"].unique())
    filter_region = st.multiselect("Filter nach Lokalisation", df["Region"].unique())
    filter_pain = st.multiselect("Filter nach Schmerzempfinden", df["Schmerzempfinden"].unique())
    filter_notes = st.text_input("Filter nach Begleitsymptomen (Textsuche)")
    filter_tageszeit = st.multiselect("Filter nach Tageszeit", df["Tageszeit"].unique())

    filtered_df = df.copy()
    if filter_patient:
        filtered_df = filtered_df[filtered_df["Name"].isin(filter_patient)]
    if filter_med:
        filtered_df = filtered_df[filtered_df["Medikament"].isin(filter_med)]
    if filter_region:
        filtered_df = filtered_df[filtered_df["Region"].isin(filter_region)]
    if filter_pain:
        filtered_df = filtered_df[filtered_df["Schmerzempfinden"].isin(filter_pain)]
    if filter_notes:
        filtered_df = filtered_df[filtered_df["Begleitsymptome"].str.contains(filter_notes, case=False, na=False)]
    if filter_tageszeit:
        filtered_df = filtered_df[filtered_df["Tageszeit"].isin(filter_tageszeit)]

    st.subheader("📊 Gefilterte Einträge")
    st.dataframe(filtered_df)

   # Verlauf visualisieren (NRS über Zeit)
st.subheader("📈 Verlauf der NRS-Werte")
if not filtered_df.empty:
    fig, ax = plt.subplots()

    # Zeitachse aus Datum + Uhrzeit
    ax.plot(
        filtered_df["Datum"] + " " + filtered_df["Uhrzeit"],
        filtered_df["NRS"],
        marker="o",
        color="crimson"
    )

    # Achsen und Titel
    ax.set_ylim(0, 10)
    ax.set_ylabel("NRS")

    # Patientenname(n) im Titel anzeigen
    if filter_patient:
        patient_list = ", ".join(filter_patient)
        ax.set_title(f"Schmerzverlauf über Zeit – Patient: {patient_list}")
    else:
        ax.set_title("Schmerzverlauf über Zeit")

    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.warning("Keine Einträge für die gewählten Filter gefunden.")

