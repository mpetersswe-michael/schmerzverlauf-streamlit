# 📦 Importe
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import re

# ⚙️ Seiteneinstellungen
st.set_page_config(page_title="Schmerzverlauf", layout="centered")

# 🔐 Passwortschutz über st.secrets
try:
    PASSWORT = st.secrets["app_password"]
except Exception as e:
    st.error("⚠️ Passwort nicht gefunden. Bitte im Secrets-Manager hinterlegen.")
    st.stop()

# 🧠 Session-Initialisierung
if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False

# 🚪 Sidebar: Login/Logout
with st.sidebar:
    st.markdown("### Zugang")
    if st.session_state.eingeloggt:
        st.markdown("✅ Eingeloggt als Michael")
        if st.button("🚪 Logout"):
            st.session_state.eingeloggt = False
            st.toast("Erfolgreich ausgeloggt ✅")
            st.rerun()
    else:
        st.markdown("🔒 Nicht eingeloggt")

# 🔐 Login-Fenster
if not st.session_state.eingeloggt:
    st.title("🔐 Login erforderlich")
    pw = st.text_input("Passwort eingeben:", type="password")
    if pw and pw == PASSWORT:
        st.session_state.eingeloggt = True
        st.toast("Login erfolgreich ✅")
        st.rerun()
    elif pw and pw != PASSWORT:
        st.error("❌ Falsches Passwort")
    st.stop()

# 🔧 Konstanten
DATEIPFAD = "schmerzverlauf.csv"
SPALTEN = [
    "RowID", "Uhrzeit", "Name", "Region", "Schmerzempfinden",
    "Intensität", "Medikament", "Dosierung", "Einheit",
    "Zeitpunkt", "Tageszeit", "Notizen", "IstTest"
]

# Hilfsfunktionen
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
        if "RowID" not in df.columns or df["RowID"].isna().any():
            df["RowID"] = range(1, len(df) + 1)
            df.to_csv(pfad, index=False)
        if "IstTest" in df.columns:
            df["IstTest"] = df["IstTest"].fillna("").astype(str)
        return df[spalten]
    except Exception as e:
        st.warning(f"⚠️ Fehler beim Laden der CSV: {e}")
        return pd.DataFrame(columns=spalten)

def naechste_rowid(pfad):
    try:
        df = pd.read_csv(pfad)
        if "RowID" in df.columns and not df.empty:
            return int(pd.to_numeric(df["RowID"], errors="coerce").max()) + 1
    except:
        pass
    return 1

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

# Tabs
st.title("📈 Schmerzverlauf erfassen und visualisieren")
tab1, tab2, tab3 = st.tabs(["Eingabe", "Daten & Filter", "Verwaltung"])

# Tab 1: Eingabe
with tab1:
    with st.form("eingabeformular"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name (Patient)")
            region = st.text_input("Körperregion (Freitext)")
            schmerz = st.text_input("Schmerzempfinden (Freitext)")
            intensitaet = st.number_input("NRS (0–10)", min_value=0, max_value=10, step=1)
            tageszeit = st.text_input("Tageszeit (Freitext)")
        with col2:
            medikament = st.text_input("Medikament (Freitext)")
            dosierung = st.text_input("Dosierung (z. B. 400 oder 400mg)")
            einheit = st.text_input("Einheit (z. B. mg, Tablette…)")
            zeitpunkt = st.text_input("Zeitpunkt (Freitext)")
            notizen = st.text_area("Begleitsymptome / Notizen", height=100)

        dry_run = st.checkbox("Dry-run aktivieren (keine Speicherung)")
        speichern = st.form_submit_button("Speichern / Anzeigen")

    if speichern:
        uhrzeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fehler = eingaben_pruefen(name, intensitaet, dosierung)
        if fehler:
            for f in fehler:
                st.error(f)
        else:
            dosierung_clean, einheit_clean = dosierung_und_einheit_trennen(dosierung, einheit)
            row_id = naechste_rowid(DATEIPFAD)
            ist_test = "Ja" if dry_run else ""
            eintrag = {
                "RowID": row_id,
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
                "Notizen": notizen.strip(),
                "IstTest": ist_test
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

# Tab 2: Daten & Filter
with tab2:
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

# Tab 3: Verwaltung
with tab3:
    st.subheader("🗑️ Verwaltung: Einträge löschen")
    df_admin = daten_laden(DATEIPFAD, SPALTEN)

    if df_admin.empty:
        st.info("Keine Einträge vorhanden.")
    else:
        st.caption("Wähle die zu löschenden Einträge über ihre RowID.")
        st.dataframe(
            df_admin[["RowID","Uhrzeit","Name","Region","Schmerzempfinden","Intensität","Medikament","Dosierung","IstTest"]],
            use_container_width=True
        )

        ids = st.multiselect("RowIDs zum Löschen wählen", options=df_admin["RowID"].tolist())
        sicher = st.checkbox("Ich bestätige die Löschung der ausgewählten Einträge")

        colA, colB = st.columns(2)
        with colA:
            if st.button("Ausgewählte Einträge löschen", type="primary", disabled=not (ids and sicher)):
                try:
                    df_rest = df_admin[~df_admin["RowID"].isin(ids)].copy()
                    df_rest.to_csv(DATEIPFAD, index=False)
                    st.success(f"✅ {len(ids)} Einträge gelöscht.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Fehler beim Löschen: {e}")

        with colB:
            if st.button("Alle Testeinträge (IstTest=Ja) löschen"):
                try:
                    df_rest = df_admin[df_admin["IstTest"] != "Ja"].copy()
                    df_rest.to_csv(DATEIPFAD, index=False)
                    st.success("✅ Alle Testeinträge gelöscht.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Fehler beim Löschen: {e}")













