import io
import os
import base64
import datetime as dt
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

# ----------------------------
# Konfiguration & Konstanten
# ----------------------------
DATA_FILE = "data.csv"

DEFAULT_COLUMNS = [
    "Name",
    "Datum",
    "Schmerzintensität",
    "Bemerkung",
    "Schmerzsituation"
]

PAIN_SITUATIONS = [
    "Vor Einnahme",
    "Nach Einnahme",
    "Stabil",
    "Instabil"
]

# Demo-Login-Daten (einfach, ohne Backend)
VALID_USERS = {
    "admin": "admin123",
    "michael": "pain2025"
}

SESSION_KEY_AUTH = "is_authenticated"
SESSION_KEY_USER = "username"

# ----------------------------
# Hilfsfunktionen: Daten
# ----------------------------
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        # Spalten sicherstellen
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        # Datum normalisieren
        try:
            df["Datum"] = pd.to_datetime(df["Datum"]).dt.date
        except Exception:
            pass
        return df[DEFAULT_COLUMNS]
    else:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_data(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")

def append_entry(df: pd.DataFrame,
                 name: str,
                 date_val: dt.date,
                 intensity: int,
                 note: str,
                 situation: str) -> pd.DataFrame:
    new_row = {
        "Name": name.strip(),
        "Datum": date_val,
        "Schmerzintensität": intensity,
        "Bemerkung": note.strip(),
        "Schmerzsituation": situation
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

def filter_by_name(df: pd.DataFrame, name_filter: str) -> pd.DataFrame:
    if not name_filter:
        return df.copy()
    return df[df["Name"].str.contains(name_filter, case=False, na=False)].copy()

# ----------------------------
# Hilfsfunktionen: Visualisierung
# ----------------------------
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
# PDF-Export (fpdf, Cloud-freundlich)
# ----------------------------
def build_pdf_fpdf(df_filtered: pd.DataFrame,
                   chart_png: io.BytesIO,
                   name_filter: str) -> io.BytesIO:
    # Diagramm temporär schreiben für fpdf.image()
    chart_path = "chart_temp.png"
    with open(chart_path, "wb") as f:
        f.write(chart_png.getbuffer())

    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Titelbereich
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 8, txt="Pain Tracking Bericht", ln=True)
    pdf.set_font("Arial", size=11)
    subtitle = f"Filter: Name enthält '{name_filter}'" if name_filter else "Filter: keiner"
    pdf.cell(0, 7, txt=subtitle, ln=True)
    pdf.cell(0, 7, txt=f"Generiert am {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)

    # Diagramm
    pdf.ln(4)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 7, txt="Diagramm", ln=True)
    pdf.image(chart_path, x=10, w=190)  # Höhe automatisch

    # Daten
    pdf.ln(4)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 7, txt="Daten (gefiltert)", ln=True)
    pdf.set_font("Arial", size=9)

    if df_filtered.empty:
        pdf.cell(0, 6, txt="Keine Daten vorhanden.", ln=True)
    else:
        header_line = " | ".join(DEFAULT_COLUMNS)
        pdf.multi_cell(0, 5, txt=header_line)
        for _, row in df_filtered.iterrows():
            line = " | ".join(str(row.get(col, "")) for col in DEFAULT_COLUMNS)
            pdf.multi_cell(0, 5, txt=line)

    # Ausgabe als Bytes
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest="S").encode("latin-1")  # fpdf liefert str; encode für Bytes
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)

    # Cleanup temp
    try:
        os.remove(chart_path)
    except Exception:
        pass

    return pdf_output

# ----------------------------
# Auth: Login/Logout (Session-State)
# ----------------------------
def login_form():
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Einloggen")
        if submit:
            if username in VALID_USERS and VALID_USERS[username] == password:
                st.session_state[SESSION_KEY_AUTH] = True
                st.session_state[SESSION_KEY_USER] = username
                st.success("Erfolgreich eingeloggt.")
                st.rerun()
            else:
                st.error("Ungültige Zugangsdaten.")

def logout_button():
    if st.session_state.get(SESSION_KEY_AUTH, False):
        st.caption(f"Eingeloggt als: {st.session_state.get(SESSION_KEY_USER)}")
        if st.button("Logout"):
            st.session_state[SESSION_KEY_AUTH] = False
            st.session_state[SESSION_KEY_USER] = None
            st.success("Abgemeldet.")
            st.rerun()

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Pain Tracking", layout="wide")
st.title("Pain Tracking – Login, Erfassung, Export")

# Auth-Gate
if not st.session_state.get(SESSION_KEY_AUTH, False):
    login_form()
    st.stop()

logout_button()

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
        errors = []
        if not name.strip():
            errors.append("Name ist erforderlich.")
        if situation not in PAIN_SITUATIONS:
            errors.append("Ungültige Schmerzsituation.")
        if errors:
            st.error("Bitte korrigieren:\n- " + "\n- ".join(errors))
        else:
            df = append_entry(df, name, date_val, intensity, note, situation)
            save_data(df)
            st.success("Eintrag gespeichert ✅ (append-only)")

st.divider()

# Ansicht + Export
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

st.subheader("PDF-Export und Ansicht")
col_exp, col_hint = st.columns([1, 1])

with col_exp:
    pdf_buf = build_pdf_fpdf(df_filtered, chart_png, filter_name)

    st.download_button(
        "PDF herunterladen",
        data=pdf_buf,
        file_name=f"pain_tracking_{dt.date.today()}.pdf",
        mime="application/pdf"
    )

    # Direkte Ansicht via iframe
    pdf_bytes = pdf_buf.getvalue()
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="520" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

with col_hint:
    st.markdown("**Druck-Hinweis**")
    st.info("Zum Drucken die PDF in der Ansicht öffnen und im Browser drucken (Strg+P bzw. ⌘+P). "
            "Die Datei kann manuell am gewünschten Ort gespeichert werden.")




































