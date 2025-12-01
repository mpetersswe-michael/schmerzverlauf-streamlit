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

PAIN_COLUMNS = ["Name", "Datum", "Intensität", "Körperregion", "Bemerkung", "Situation"]
MED_COLUMNS = ["Name", "Datum", "Medikament", "Dosierung", "Art"]

PAIN_SITUATIONS = ["Vor Einnahme", "Nach Einnahme", "Stabil", "Instabil"]
MED_TYPES = ["Bedarfsmedikation", "Dauermedikation", "Akut", "Langzeit"]

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
    if not name_filter:
        return df.copy()
    return df[df["Name"].str.contains(name_filter, case=False, na=False)].copy()

def plot_pain(df_filtered):
    buf = io.BytesIO()
    if df_filtered.empty:
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
# Tab 1: Schmerz-Eintrag
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
        situation = st.radio("Situation", PAIN_SITUATIONS, horizontal=True)
        note = st.text_area("Bemerkung (optional)", height=80)
        submit = st.form_submit_button("Speichern (append-only)")

        if submit:
            if not name.strip():
                st.error("Name ist erforderlich.")
            else:
                new_row = {
                    "Name": name.strip(),
                    "Datum": date_val,
                    "Intensität": intensity,
                    "Körperregion": region.strip(),
                    "Bemerkung": note.strip(),
                    "Situation": situation
                }
                df_pain = append_row(df_pain, new_row)
                save_data(df_pain, DATA_FILE_PAIN)
                st.success("Eintrag gespeichert ✅")

# ----------------------------
# Tab 2: Medikamenten-Eintrag
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
            if not name.strip() or not med.strip():
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
# Tab 3: Verlauf / Export
# ----------------------------
with tab3:
    st.subheader("Verlauf und Export")
    df_pain = load_data(DATA_FILE_PAIN, PAIN_COLUMNS)

    filter_name = st.text_input("Filter nach Name (optional)", value="")
    df_filtered = filter_by_name(df_pain, filter_name)

    c_table, c_chart = st.columns([3, 2])
    with c_table:
        st.markdown("**Gefilterte Tabelle**")
        st.dataframe(df_filtered, use_container_width=True, height=380)

        csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "CSV herunterladen",
            data=csv_bytes,
            file_name=f"pain_tracking_{dt.date.today()}.csv",
            mime="text/csv"
        )

    with c_chart:
        st.markdown("**Diagramm (Schmerzverlauf)**")
        chart_png = plot_pain(df_filtered)
        st.image(chart_png, caption="Liniendiagramm", use_column_width=True)

    st.divider()
    st.subheader("Druck-Hinweis")
    st.info("Zum Drucken bitte die Seite über den Browser drucken (Strg+P bzw. ⌘+P). "
            "Die Tabelle und das Diagramm sind direkt sichtbar.")
























