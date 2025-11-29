import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Seiteneinstellungen
st.set_page_config(page_title="Schmerzverlauf", layout="centered")
st.title("📈 Schmerzverlauf erfassen und visualisieren")

# CSV-Datei und Spaltenüberschriften
DATEIPFAD = "schmerzverlauf.csv"
SPALTEN = [
    "Uhrzeit", "Name", "Region", "Schmerzempfinden",
    "Intensität", "Medikament", "Dosierung", "Einheit",
    "Zeitpunkt", "Tageszeit", "Notizen"
]

# Hilfsfunktionen
def csv_erzeugen_wenn_fehlt(pfad, spalten):
    if not os.path.exists(pfad) or os.path.getsize(pfad) == 0:
        pd.DataFrame(columns=spalten).to_csv(pfad, index=False)

def eingaben_pruefen(name, intensitaet, dosierung):
    fehler = []
    if not name.strip():
        fehler.append("⚠️ Bitte den Namen eingeben.")
    if intensitaet is None:
        fehler.append("⚠️ Bitte die Schmerzintensität (NRS) wählen.")
    if dosierung.strip() and any(z in dosierung for z in [";", "|"]):
        fehler.append("⚠️ Dosierung enthält ungültige Zeichen.")
    return fehler

def zeile_anhaengen(pfad, spalten, daten):
    csv_erzeugen_wenn_fehlt(pfad, spalten)
    pd.DataFrame([daten], columns=spalten).to_csv(pfad, mode="a", index=False, header=False)

def daten_laden(pfad, spalten):
    if os.path.exists(pfad) and os.path.getsize(pfad) > 0:
        try:
            df = pd.read_csv(pfad)
            fehlende = [s for s in spalten if s not in df.columns]
            for s in fehlende:
                df[s] = ""
            return df[spalten]
        except Exception as e:
            st.warning(f"⚠️ Fehler beim Laden der CSV: {e}")
            return pd.DataFrame(columns=spalten)
    return pd.DataFrame(columns=spalten)

# Eingabeformular
with st.form("eingabeformular"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name (Patient)")
        region = st.selectbox("Körperregion", ["Kopf", "Rücken", "Bein", "Arm", "Bauch"])
        schmerz = st.radio("Schmerzempfinden", ["Stechend", "Dumpf", "Brennend", "Ziehend"])
        intensitaet = st.slider("NRS (0–10)", 0, 10, 5)
        tageszeit = st.selectbox("Tageszeit", ["Morgen", "Mittag", "Abend", "Nacht"])
    with col2:
        medikament = st.text_input("Medikament")
        dosierung = st.text_input("Dosierung")
        einheit = st.selectbox("Einheit", ["mg", "Tablette", "Ampulle", "Tropfen"])
        zeitpunkt = st.radio("Zeitpunkt", ["Vor Einnahme", "Nach Einnahme"])
        notizen = st.text_area("Begleitsymptome / Notizen", height=100)

    dry_run = st.checkbox("Dry-run aktivieren (keine Speicherung)")
    speichern = st.form_submit_button("Speichern / Anzeigen")

# Verarbeitung
if speichern:
    uhrzeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fehler = eingaben_pruefen(name, intensitaet, dosierung)

    if fehler:
        for f in fehler:
            st.error(f)
    else:
        eintrag = {
            "Uhrzeit": uhrzeit,
            "Name": name.strip(),
            "Region": region,
            "Schmerzempfinden": schmerz,
            "Intensität": intensitaet,
            "Medikament": medikament.strip(),
            "Dosierung": dosierung.strip(),
            "Einheit": einheit,
            "Zeitpunkt": zeitpunkt,
            "Tageszeit": tageszeit,
            "Notizen": notizen.strip()
        }

        if dry_run:
            st.info("🔒 Dry-run aktiv: Daten wurden NICHT gespeichert.")
        else:
            try:
                zeile_anhaengen(DATEIPFAD, SPALTEN, eintrag)
                st.success("✅ Eintrag gespeichert.")
            except Exception as e:
                st.error(f"❌ Fehler beim Speichern: {e}")

        st.subheader("📝 Zusammenfassung")
        st.write(pd.DataFrame([eintrag]))

# Datenanzeige und Diagramm
st.divider()
st.subheader("📋 Gespeicherte Einträge")
df = daten_laden(DATEIPFAD, SPALTEN)

if df.empty:
    st.info("Noch keine Daten vorhanden.")
else:
    st.dataframe(df, use_container_width=True)

    try:
        df["Uhrzeit_dt"] = pd.to_datetime(df["Uhrzeit"], errors="coerce")
        df = df.dropna(subset=["Uhrzeit_dt"]).sort_values("Uhrzeit_dt")

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df["Uhrzeit_dt"], df["Intensität"], marker="o")
        ax.set_title("Schmerzintensität über Zeit")
        ax.set_xlabel("Uhrzeit")
        ax.set_ylabel("NRS (0–10)")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"⚠️ Diagramm konnte nicht erstellt werden: {e}")




