import io
import os
import datetime as dt
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Konfiguration
# ----------------------------
DATA_FILE_PAIN = "pain_data.csv"
DATA_FILE_MED = "med_data.csv"
VALID_PASSWORD = "QM1514"
SESSION_KEY_AUTH = "is_authenticated"

# Tab 1: Schmerz-Eintrag – vollständiges Feldset
PAIN_COLUMNS = [
    "Name",
    "Datum",
    "Intensität",
    "Körperregion",
    "Schmerzempfinden",
    "Begleitsymptome",
    "Tageszeit",
    "Schmerzeintritt",
    "Schmerzsituation",
    "Bemerkung"
]

# Tab 2: Medikamente – reduziertes Feldset
MED_COLUMNS = ["Name", "Datum", "Medikament", "Dosierung", "Art"]

# Auswahllisten
SCHMERZEMPFINDEN_OPTS = ["brennend", "dumpf", "stechend", "ziehend", "pochend"]
BEGLEITSYMPTOME_OPTS = ["Übelkeit", "Schwindel", "Müdigkeit", "Fieber", "Erbrechen"]
TAGESZEIT_OPTS = ["morgens", "mittags", "abends", "nachts"]
MED_TYPES = ["Bedarfsmedikation", "Dauermedikation"]

# ----------------------------
# Login / Logout
# ----------------------------
def login_form():
    st.subheader("Login")
    with st.form("login_form"):
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Einloggen")
        if submit:
            if password == VALID_PASSWORD:
                st.session_state[SESSION_KEY_AUTH] = True
                st.success("Erfolgreich eingeloggt.")
                st.rerun()
            else:
                st.error("Ungültiges Passwort.")

def sidebar_logout():
    with st.sidebar:
        st.markdown("### Navigation")
        if st.session_state.get(SESSION_KEY_AUTH, False):
            if st.button("Logout"):
                st.session_state[SESSION_KEY_AUTH] = False
                st.success("Abgemeldet.")
                st.rerun()

# ----------------------------
# Datenfunktionen
# ----------------------------
def load_data(path, columns):
    if os.path.exists(path):
        df = pd.read_csv(path, encoding="utf-8")
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        try:
            df["Datum"] = pd.to_datetime(df["Datum"]).dt.date
        except Exception:
            pass
        return df[columns]
    else:
        return pd.DataFrame(columns=columns)

def save_data(df, path):
    df.to_csv(path, index=False, encoding="utf-8")

def append_row(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)

def filter_by_name(df, name_filter):
    if "Name" not in df.columns:
        return df.copy()
    if not name_filter:
        return df.copy()
    return df[df["Name"].str.contains(name_filter, case=False, na=False)].copy()

def plot_pain(df_filtered):
    buf = io.BytesIO()
    if df_filtered.empty or "Intensität" not in df_filtered.columns:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.text(0.5, 0.5, "Keine Daten für Diagramm", ha="center", va="center")
        ax.axis("off")
    else:
        dfp = df_filtered.copy()
        try:
            dfp["Datum"] = pd.to_datetime(dfp["Datum"])
        except Exception:
            pass
        dfp = dfp.sort_values("Datum")
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.plot(dfp["Datum"], dfp["Intensität"], marker="o", linewidth=2, color="#1f77b4")
        ax.set_title("Schmerzverlauf")
        ax.set_xlabel("Datum")
        ax.set_ylabel("Intensität (0–10)")
        ax.set_ylim(0, 10)
        ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf

# ----------------------------
# UI Start
# ----------------------------
st.set_page_config(page_title="Pain Tracking", layout="wide")
st.title("Pain Tracking – Login, Erfassung, Verlauf")

if not st.session_state.get(SESSION_KEY_AUTH, False):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_form()
    st.stop()

sidebar_logout()

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3 = st.tabs(["📋 Eintrag", "💊 Medikamente", "📈 Verlauf"])

# ----------------------------
# Tab 1: Schmerz-Eintrag (mit Körperregion, Schmerzempfinden, Begleitsymptome, Tageszeit, Schmerzeintritt, Schmerzsituation)
# ----------------------------
with tab1:
    st.subheader("Neuer Schmerz-Eintrag")
    df_pain = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)

    with st.form("pain_form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            name = st.text_input("Name", value="", placeholder="Patientenname")
        with col2:
            date_val = st.date_input("Datum", value=dt.date.today())
        with col3:
            intensity = st.slider("Intensität (0–10)", min_value=0, max_value=10, value=5)

        region = st.text_input("Körperregion", placeholder="z. B. Kopf, Rücken, Bein")

        pain_feel = st.multiselect("Schmerzempfinden", options=SCHMERZEMPFINDEN_OPTS)
        symptoms = st.multiselect("Begleitsymptome", options=BEGLEITSYMPTOME_OPTS)

        time_of_day = st.selectbox("Tageszeit", options=TAGESZEIT_OPTS, index=0)

        st.markdown("**Schmerzeintritt**")
        entry_before = st.checkbox("Schmerzeintritt vor Einnahme eines Medikamentes")
        entry_after = st.checkbox("Schmerzeintritt nach Einnahme eines Medikamentes")

        st.markdown("**Schmerzsituation**")
        situation_stable = st.checkbox("Schmerzsituation ist stabil")
        situation_unstable = st.checkbox("Schmerzsituation ist instabil")

        note = st.text_area("Bemerkung (optional)", height=80)

        submit = st.form_submit_button("Speichern (append-only)")

        if submit:
            if not name.strip():
                st.error("Name ist erforderlich.")
            else:
                entry_list = []
                if entry_before:
                    entry_list.append("vor Einnahme eines Medikamentes")
                if entry_after:
                    entry_list.append("nach Einnahme eines Medikamentes")
                situation_list = []
                if situation_stable:
                    situation_list.append("stabil")
                if situation_unstable:
                    situation_list.append("instabil")

                new_row = {
                    "Name": name.strip(),
                    "Datum": date_val,
                    "Intensität": intensity,
                    "Körperregion": region.strip(),
                    "Schmerzempfinden": ", ".join(pain_feel),
                    "Begleitsymptome": ", ".join(symptoms),
                    "Tageszeit": time_of_day,
                    "Schmerzeintritt": ", ".join(entry_list),
                    "Schmerzsituation": ", ".join(situation_list),
                    "Bemerkung": note.strip(),
                }
                df_pain = append_row(df_pain, new_row)
                save_data(df_pain, DATA_FILE_PAIN)
                st.success("Eintrag gespeichert ✅")

# ----------------------------
# Tab 2: Medikamenten-Eintrag (ohne Patientenname, Art mit Mehrfachauswahl)
# ----------------------------
with tab2:
    st.subheader("Medikamenten-Eintrag")
    df_med = load_data(DATA_FILE_MED, MED_COLUMNS)

    with st.form("med_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input("Name", value="", placeholder="Patientenname")
        with col2:
            date_val = st.date_input("Datum", value=dt.date.today())

        med = st.text_input("Medikament")
        dose = st.text_input("Dosierung")
        med_types_selected = st.multiselect("Art", options=MED_TYPES)

        submit = st.form_submit_button("Speichern (append-only)")

        if submit:
            if not med.strip() or not name.strip():
                st.error("Name und Medikament sind erforderlich.")
            else:
                new_row = {
                    "Name": name.strip(),
                    "Datum": date_val,
                    "Medikament": med.strip(),
                    "Dosierung": dose.strip(),
                    "Art": ", ".join(med_types_selected)
                }
                df_med = append_row(df_med, new_row)
                save_data(df_med, DATA_FILE_MED)
                st.success("Eintrag gespeichert ✅")

# ----------------------------
# Tab 3: Verlauf / Export – Medikamente oben, Schmerzverlauf mittig, Diagramm unten
# ----------------------------
with tab3:
    st.subheader("Verlauf und Export")

    # Filterfeld für beide Tabellen
    filter_name = st.text_input("Filter nach Name (optional)", value="")

    # Medikamentenliste zuerst
    st.markdown("### Verabreichte Medikamente und den Patientennamen")
    df_med = load_data(DATA_FILE_MED, MED_COLUMNS)
    df_filtered_med = filter_by_name(df_med, filter_name)
    st.dataframe(df_filtered_med, use_container_width=True, height=240)

    csv_med = df_filtered_med.to_csv(index=False).encode("utf-8")
    st.download_button(
        "CSV Medikamente herunterladen",
        data=csv_med,
        file_name=f"medications_{dt.date.today()}.csv",
        mime="text/csv"
    )

    st.divider()

    # Schmerzverlauf-Tabelle
    st.markdown("### Gefilterte Tabelle – Schmerzverlauf")
    df_pain = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)
    df_filtered_pain = filter_by_name(df_pain, filter_name)
    st.dataframe(df_filtered_pain, use_container_width=True, height=300)

    csv_pain = df_filtered_pain.to_csv(index=False).encode("utf-8")
    st.download_button(
        "CSV Schmerzverlauf herunterladen",
        data=csv_pain,
        file_name=f"pain_tracking_{dt.date.today()}.csv",
        mime="text/csv"
    )

    st.divider()

    # Diagramm ganz unten
    st.markdown("### Diagramm – Schmerzverlauf")
    chart_png = plot_pain(df_filtered_pain)
    st.image(chart_png, caption="Liniendiagramm", use_column_width=True)

    st.divider()
    st.subheader("Druck-Hinweis")
    st.info("Zum Drucken bitte die Seite über den Browser drucken (Strg+P bzw. ⌘+P). "
            "Die Tabellen und das Diagramm sind direkt sichtbar.")








