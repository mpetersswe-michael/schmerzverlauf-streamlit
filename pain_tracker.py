import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import re

# Seiteneinstellungen
st.set_page_config(page_title="Schmerzverlauf", layout="centered")

# 🔐 Passwortschutz
PASSWORT = "QM1514"  # ← hier dein Passwort eintragen

if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False

with st.sidebar:
    st.markdown("### Zugang")
    if st.session_state.eingeloggt:
        if st.button("Logout"):
            st.session_state.eingeloggt = False
            st.success("🔓 Ausgeloggt")

if not st.session_state.eingeloggt:
    st.title("🔒 Login erforderlich")
    pw = st.text_input("Passwort eingeben:", type="password")
    if pw and pw == PASSWORT:
        st.session_state.eingeloggt = True
        st.success("✅ Login erfolgreich – bitte oben auf „Neu laden“ klicken.")
    elif pw and pw != PASSWORT:
        st.error("❌ Falsches Passwort")
    st.stop()

# 🔧 Konstanten
DATEIPFAD = "schmerzverlauf.csv"
SPALTEN = [
    "Uhrzeit", "Name", "Region", "Schmerzempfinden",
    "Intensität", "Medikament", "Dosierung", "Einheit",
    "Zeitpunkt", "Tageszeit", "Notizen"
]

# 🔧 Hilfsfunktionen
def csv_erzeugen_wenn_fehlt(pfad, spalten):
    if not os.path.exists(pfad) or os.path.getsize(pfad) == 0:
        pd.DataFrame(columns=spalten).to_csv(pfad, index=False)

def eingaben_pruefen(name, intensitaet, dosierung):
    fehler = []
    if not name.strip():
        fehler.append("⚠️ Bitte den Namen eingeben.")
    if intensitaet is None:
        fehler.append("⚠️ Bitte die Schmerzintensität wählen.")
    if dosierung.strip() and any(z in dosierung for z in [";", "|"]):
        fehler.append("⚠️ Dosierung enthält ungültige Zeichen.")
    return fehler

def dosierung_und_einheit_trennen(dosierung, einheit):
    m = re.match(r"^\s*(\d+(?:[\.,]\d+)?)\s*([A-Za-zäöüÄÖÜ]*)\s*$", dosierung.strip())
    if m:
        zahl = m.group(1).replace(",", ".")
        auto_einheit = m.group(2)
        final_einheit = einheit if einheit else auto_einheit
        return zahl, final_einheit
    return dosierung.strip(), einheit

def zeile_anhaengen(pfad, spalten, daten):
    csv_erzeugen_wenn_fehlt(pfad, spalten)
    pd.DataFrame([daten], columns=spalten).to_csv(pfad, mode="a", index=False, header=False)

def daten_laden(pfad, spalten):
    csv_erzeugen_wenn_fehlt(pfad, spalten)
    try:
        df = pd.read_csv(pfad)
        for s in spalten:
            if s not in df.columns:
                df[s] = ""
        return df[spalten]
    except Exception as e:
        st.warning(f"⚠️ Fehler beim Laden der CSV: {e}")
        return pd.DataFrame(columns=spalten)

# 📝 Eingabeformular
st.title("📈 Schmerzverlauf erfassen und visualisieren")

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
        dosierung = st.text_input("Dosierung (z. B. 400)")
        einheit = st.selectbox("Einheit", ["mg", "Tablette", "Ampulle", "Tropfen", ""])
        zeitpunkt = st.radio("Zeitpunkt", ["Vor Einnahme", "Nach Einnahme"])
        notizen = st.text_area("Begleitsymptome / Notizen", height=100)

    dry_run = st.checkbox("Dry-run aktivieren (keine Speicherung)")
    speichern = st.form_submit_button("Speichern / Anzeigen")

# 💾 Verarbeitung
if speichern:
    uhrzeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fehler = eingaben_pruefen(name, intensitaet, dosierung)

    if fehler:
        for f in fehler:
            st.error(f)
    else:
        dosierung_clean, einheit_clean = dosierung_und_einheit_trennen(dosierung, einheit)
        eintrag = {
            "Uhrzeit": uhrzeit,
            "Name": name.strip(),
            "Region": region,
            "Schmerzempfinden": schmerz,
            "Intensität": intensitaet,
            "Medikament": medikament.strip(),
            "Dosierung": dosierung_clean,
            "Einheit": einheit_clean,
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

# 📋 Datenanzeige & Filter
st.divider()
st.subheader("📋 Gespeicherte Einträge")
df = daten_laden(DATEIPFAD, SPALTEN)

if df.empty:
    st.info("Noch keine Daten vorhanden.")
else:
    st.subheader("🔍 Filteroptionen")
    name_filter = st.text_input("Filter: Name enthält")
    region_filter = st.selectbox("Filter: Region", ["Alle"] + sorted(df["Region"].dropna().unique().tolist()))
    zeitpunkt_filter = st.selectbox("Filter: Zeitpunkt", ["Alle"] + sorted(df["Zeitpunkt"].dropna().unique().tolist()))
    tageszeit_filter = st.selectbox("Filter: Tageszeit", ["Alle"] + sorted(df["Tageszeit"].dropna().unique().tolist()))

    filtered_df = df.copy()
    if name_filter:
        filtered_df = filtered_df[filtered_df["Name"].str.contains(name_filter, case=False, na=False)]
    if region_filter != "Alle":
        filtered_df = filtered_df[filtered_df["Region"] == region_filter]
    if zeitpunkt_filter != "Alle":
        filtered_df = filtered_df[filtered_df["Zeitpunkt"] == zeitpunkt_filter]
    if tageszeit_filter != "Alle":
        filtered_df = filtered_df[filtered_df["Tageszeit"] == tageszeit_filter]

    st.dataframe(filtered_df, use_container_width=True)

      st.download_button(
        label="📥 CSV herunterladen",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="schmerzverlauf_auszug.csv",
        mime="text/csv"
    )

    try:
        plot_df = filtered_df.copy()
        plot_df["Uhrzeit_dt"] = pd.to_datetime(plot_df["Uhrzeit"], errors="coerce")
        plot_df = plot_df.dropna(subset=["Uhrzeit_dt"]).sort_values("Uhrzeit_dt")
        y = plot_df["Intensität"].astype(float)

        if not plot_df.empty:
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(plot_df["Uhrzeit_dt"], y, marker="o")
            ax.set_title("Schmerzintensität über Zeit")
            ax.set_xlabel("Uhrzeit")
            ax.set_ylabel("NRS (0–10)")
            ax.grid(True, alpha=0.3)
            ax.set_ylim(max(0, y.min() - 0.5), min(10, y.max() + 0.5))
            ax.set_xlim(plot_df["Uhrzeit_dt"].min() - pd.Timedelta(minutes=1),
                        plot_df["Uhrzeit_dt"].max() + pd.Timedelta(minutes=1))
            fig.autofmt_xdate()
            st.pyplot(fig)
        else:
            st.info("Keine gültigen Zeitpunkte für die Visualisierung.")
    except Exception as e:
        st.warning(f"⚠️ Diagramm konnte nicht erstellt werden: {e}")

