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
            st.experimental_rerun()
    else:
        st.markdown("🔒 Nicht eingeloggt")

if not st.session_state.eingeloggt:
    st.title("🔐 Login erforderlich")
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

def eingaben_pruefen(name, intensitaet, dosierung):
    fehler = []
    if not name.strip():
        fehler.append("⚠️ Bitte den Namen eingeben.")
    if intensitaet is None:
        fehler.append("⚠️ Bitte die Schmerzintensität angeben.")
    if dosierung.strip() and any(z in dosierung for z in [";", "|"]):
        fehler.append("⚠️ Dosierung enthält ungültige Zeichen.")
    return fehler

def dosierung_und_einheit_trennen(dosierung, einheit):
    # Erlaubt "400 mg" oder "400mg" oder "400"
    m = re.match(r"^\s*(\d+(?:[\.,]\d+)?)\s*([A-Za-zäöüÄÖÜ]*)\s*$", dosierung.strip())
    if m:
        zahl = m.group(1).replace(",", ".")
        auto_einheit = m.group(2)
        final_einheit = einheit.strip() if einheit.strip() else auto_einheit
        return zahl, final_einheit
    return dosierung.strip(), einheit.strip()

def zeile_anhaengen(pfad, spalten, daten):
    csv_erzeugen_wenn_fehlt(pfad, spalten)
    pd.DataFrame([daten], columns=spalten).to_csv(pfad, mode="a", index=False, header=False)

# Daten laden (für optionale Auswahllisten aus vorhandenen Werten)
df_all = daten_laden(DATEIPFAD, SPALTEN)

# 📝 Eingabeformular (nur Freitext, optional: Auswahl aus vorhandenen Werten)
st.title("📈 Schmerzverlauf erfassen und visualisieren")

with st.form("eingabeformular"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name (Patient)", value="")
        region = st.text_input("Körperregion (Freitext)", value="")
        schmerz = st.text_input("Schmerzempfinden (Freitext)", value="")
        intensitaet = st.number_input("NRS (0–10)", min_value=0, max_value=10, step=1)
        tageszeit = st.text_input("Tageszeit (Freitext)", value="")
    with col2:
        medikament = st.text_input("Medikament (Freitext)", value="")
        dosierung = st.text_input("Dosierung (z. B. 400 oder 400mg)", value="")
        einheit = st.text_input("Einheit (z. B. mg, Tablette…)", value="")
        zeitpunkt = st.text_input("Zeitpunkt (Freitext, z. B. Vor Einnahme, Nach Einnahme)", value="")
        notizen = st.text_area("Begleitsymptome / Notizen", height=100)

    # Optional: Aus vorhandenen Werten wählen (ohne feste Vorgaben)
    with st.expander("Aus vorhandenen Werten wählen (optional)"):
        if not df_all.empty:
            colv1, colv2 = st.columns(2)
            with colv1:
                region_v = st.selectbox("Aus vorhandenen Regionen wählen", ["–"] + sorted(df_all["Region"].dropna().unique().tolist()))
                schmerz_v = st.selectbox("Aus vorhandenen Empfindungen wählen", ["–"] + sorted(df_all["Schmerzempfinden"].dropna().unique().tolist()))
                tageszeit_v = st.selectbox("Aus vorhandenen Tageszeiten wählen", ["–"] + sorted(df_all["Tageszeit"].dropna().unique().tolist()))
            with colv2:
                medikament_v = st.selectbox("Aus vorhandenen Medikamenten wählen", ["–"] + sorted(df_all["Medikament"].dropna().unique().tolist()))
                einheit_v = st.selectbox("Aus vorhandenen Einheiten wählen", ["–"] + sorted(df_all["Einheit"].dropna().unique().tolist()))
                zeitpunkt_v = st.selectbox("Aus vorhandenen Zeitpunkten wählen", ["–"] + sorted(df_all["Zeitpunkt"].dropna().unique().tolist()))
        else:
            st.info("Noch keine Daten vorhanden – Auswahl aus vorhandenen Werten wird angezeigt, sobald Daten gespeichert sind.")

    dry_run = st.checkbox("Dry-run aktivieren (keine Speicherung)")
    speichern = st.form_submit_button("Speichern / Anzeigen")

# 💾 Verarbeitung
if speichern:
    # Falls optionale Auswahl gewählt wurde, übernimmt sie den Freitext (nur wenn Freitext leer ist)
    if not df_all.empty:
        def prefer_val(text_val, chosen_val):
            return text_val if text_val.strip() else (chosen_val if chosen_val and chosen_val != "–" else "")
        region = prefer_val(region, locals().get("region_v", "–"))
        schmerz = prefer_val(schmerz, locals().get("schmerz_v", "–"))
        tageszeit = prefer_val(tageszeit, locals().get("tageszeit_v", "–"))
        medikament = prefer_val(medikament, locals().get("medikament_v", "–"))
        einheit = prefer_val(einheit, locals().get("einheit_v", "–"))
        zeitpunkt = prefer_val(zeitpunkt, locals().get("zeitpunkt_v", "–"))

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
            "Region": region.strip(),
            "Schmerzempfinden": schmerz.strip(),
            "Intensität": int(intensitaet),
            "Medikament": medikament.strip(),
            "Dosierung": dosierung_clean,
            "Einheit": einheit_clean,
            "Zeitpunkt": zeitpunkt.strip(),
            "Tageszeit": tageszeit.strip(),
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

# 📋 Datenanzeige & Filter (alles Freitext-basiert)
st.divider()
st.subheader("📋 Gespeicherte Einträge")
df = daten_laden(DATEIPFAD, SPALTEN)

if df.empty:
    st.info("Noch keine Daten vorhanden.")
else:
    st.subheader("🔍 Filteroptionen (Freitext)")
    name_filter = st.text_input("Filter: Name enthält")
    region_filter = st.text_input("Filter: Region enthält")
    schmerz_filter = st.text_input("Filter: Schmerzempfinden enthält")
    zeitpunkt_filter = st.text_input("Filter: Zeitpunkt enthält")
    tageszeit_filter = st.text_input("Filter: Tageszeit enthält")
    medikament_filter = st.text_input("Filter: Medikament enthält")

    filtered_df = df.copy()
    def contains(col, val):
        return filtered_df[col].str.contains(val, case=False, na=False)

    if name_filter.strip():
        filtered_df = filtered_df[contains("Name", name_filter)]
    if region_filter.strip():
        filtered_df = filtered_df[contains("Region", region_filter)]
    if schmerz_filter.strip():
        filtered_df = filtered_df[contains("Schmerzempfinden", schmerz_filter)]
    if zeitpunkt_filter.strip():
        filtered_df = filtered_df[contains("Zeitpunkt", zeitpunkt_filter)]
    if tageszeit_filter.strip():
        filtered_df = filtered_df[contains("Tageszeit", tageszeit_filter)]
    if medikament_filter.strip():
        filtered_df = filtered_df[contains("Medikament", medikament_filter)]

    st.dataframe(filtered_df, use_container_width=True)

    st.download_button(
        label="📥 CSV herunterladen",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="schmerzverlauf_auszug.csv",
        mime="text/csv"
    )

    # Diagramm
    try:
        plot_df = filtered_df.copy()
        plot_df["Uhrzeit_dt"] = pd.to_datetime(plot_df["Uhrzeit"], errors="coerce")
        plot_df = plot_df.dropna(subset=["Uhrzeit_dt"]).sort_values("Uhrzeit_dt")
        y = pd.to_numeric(plot_df["Intensität"], errors="coerce")

        if not plot_df.empty and y.notna().any():
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(plot_df["Uhrzeit_dt"], y, marker="o")
            ax.set_title("Schmerzintensität über Zeit")
            ax.set_xlabel("Uhrzeit")
            ax.set_ylabel("NRS (0–10)")
            ax.grid(True, alpha=0.3)
            ymin = max(0, (y.min() if y.notna().any() else 0) - 0.5)
            ymax = min(10, (y.max() if y.notna().any() else 10) + 0.5)
            ax.set_ylim(ymin, ymax)
            fig.autofmt_xdate()
            st.pyplot(fig)
        else:
            st.info("Keine gültigen Zeitpunkte/Intensitäten für die Visualisierung.")
    except Exception as e:
        st.warning(f"⚠️ Diagramm konnte nicht erstellt werden: {e}")





