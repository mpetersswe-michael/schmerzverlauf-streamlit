import io
import os
import datetime as dt
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Konfiguration
# ----------------------------
DATA_FILE = "data.csv"
DEFAULT_COLUMNS = ["Name", "Datum", "Schmerzintensität", "Bemerkung", "Schmerzsituation"]
PAIN_SITUATIONS = ["Vor Einnahme", "Nach Einnahme", "Stabil", "Instabil"]

# Nur ein Passwort nötig
VALID_PASSWORD = "QM1514"
SESSION_KEY_AUTH = "is_authenticated"

# ----------------------------
# Hilfsfunktionen: Daten
# ----------------------------
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        try:
            df["Datum"] = pd.to_datetime(df["Datum"]).dt.date
        except Exception:
            pass
        return df[DEFAULT_COLUMNS]
    else:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_data(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")

def append_entry(df: pd.DataFrame, name: str, date_val: dt.date,
                 intensity: int, note: str, situation: str) -> pd.DataFrame:
    new_row = {
        "Name": name.strip(),
        "Datum": date_val,
        "Schmerzintensität": intensity,
        "Bemerkung": note.strip(),
        "Schmerzsituation": situation
    }
    return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

def filter_by_name(df: pd.DataFrame, name_filter: str) -> pd.DataFrame:
    if not name_filter:
        return df.copy()
    return df[df["Name"].str.contains(name_filter, case=False, na=False)].copy()

def plot_pain_over_time(df_filtered: pd.DataFrame) -> io.BytesIO:
    buf = io.BytesIO()
    if df_filtered.empty:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.text(0.5, 0.5, "Keine Daten für Diagramm", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=150)
        buf.seek(0)
        plt.close(fig)
        return buf

    dfp = df_filtered.copy()
    try:
        dfp["Datum"] = pd.to_datetime(dfp["Datum"])
    except Exception:
        pass
    dfp = dfp.sort_values("Datum")

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(dfp["Datum"], dfp["Schmerzintensität"], marker="o", linewidth=2, color="#1f77b4")
    ax.set_title("Schmerzverlauf über Zeit")
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
# Auth: Login/Logout
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
# UI
# ----------------------------
st.set_page_config(page_title="Pain Tracking", layout="wide")
st.title("Pain Tracking – Login, Erfassung, Ansicht")
st.set_page_config(page_title="Pain Tracking", layout="wide")
st.title("Pain Tracking – Login, Erfassung, Ansicht")

# Auth-Gate mit zentralem Login
if not st.session_state.get(SESSION_KEY_AUTH, False):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_form()
    st.stop()


# Auth-Gate
if not st.session_state.get(SESSION_KEY_AUTH, False):
    login_form()
    st.stop()

sidebar_logout()

df = load_data()

# Erfassung
with st.form(key="input_form", clear_on_submit=False):
    st.subheader("Neuer Eintrag")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        name = st.text_input("Name", value="", placeholder="Patientenname")
    with col2:
        date_val = st.date_input("Datum", value=dt.date.today())
    with col3:
        intensity = st.slider("Schmerzintensität (0–10)", min_value=0, max_value=10, value=5)

    situation = st.radio("Schmerzsituation:", PAIN_SITUATIONS, horizontal=True)
    note = st.text_area("Bemerkung (optional)", height=80)

    submit = st.form_submit_button("Speichern (append-only)")
    if submit:
        if not name.strip():
            st.error("Name ist erforderlich.")
        else:
            df = append_entry(df, name, date_val, intensity, note, situation)
            save_data(df)
            st.success("Eintrag gespeichert ✅ (append-only)")

st.divider()

# Ansicht
st.subheader("Datenansicht und Diagramm")
filter_name = st.text_input("Filter nach Name (Teilstring, optional)", value="")
df_filtered = filter_by_name(df, filter_name)

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
    chart_png = plot_pain_over_time(df_filtered)
    st.image(chart_png, caption="Liniendiagramm der Schmerzintensität", use_column_width=True)

st.divider()
st.subheader("Druck-Hinweis")
st.info("Zum Drucken bitte die Seite über den Browser drucken (Strg+P bzw. ⌘+P). "
        "Die Tabelle und das Diagramm sind direkt sichtbar.")





















