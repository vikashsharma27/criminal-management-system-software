import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator
from datetime import datetime
import io
import os
import zipfile

# Folder where logo/banner images live (put your files here, next to app.py)
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "IMAGE")


def image_path(filename):
    """Return the image path if the file exists, else None."""
    path = os.path.join(IMAGE_DIR, filename)
    return path if os.path.exists(path) else None

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(page_title="Criminal Management System", page_icon="🗂️", layout="wide")

st.markdown(
    """
    <style>
        div[data-testid="stHeader"] {
            display: none !important;
        }
        div[data-testid="stToolbar"] {
            display: none !important;
        }
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
        div[data-testid="stForm"] {
            margin-top: 0 !important;
        }
        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
            background-color: #e8f8ee !important;
            color: #1f5a3d !important;
            border: 1px solid #bfe7cf !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
            background-color: #eaf2ff !important;
            color: #284a8a !important;
            border: 1px solid #bfd4ff !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
            background-color: #fdecec !important;
            color: #8a2d2d !important;
            border: 1px solid #f2b9be !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div:nth-child(4) button {
            background-color: #f3f3f3 !important;
            color: #4b4b4b !important;
            border: 1px solid #d9d9d9 !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div button:hover {
            filter: brightness(0.98);
            opacity: 1;
        }
        /* Custom Modern Dashboard Styles */
        .metric-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 1.1rem 1.2rem;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #3b82f6;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            margin-bottom: 0.8rem;
        }
        .metric-card.red { border-top-color: #ef4444; }
        .metric-card.green { border-top-color: #10b981; }
        .metric-card.purple { border-top-color: #8b5cf6; }
        .metric-card.amber { border-top-color: #f59e0b; }
        .metric-title {
            font-size: 0.8rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.3rem;
        }
        .metric-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
        }
        .metric-subtext {
            font-size: 0.82rem;
            color: #64748b;
            margin-top: 0.3rem;
            font-weight: 500;
        }
        .section-header-box {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.25rem;
            font-weight: 700;
            color: #1e293b;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }
        .filter-container {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 1.5rem;
        }
        .export-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    DB_SECRETS = st.secrets.get("database", {})
except Exception:
    DB_SECRETS = {}

DB_HOST = os.getenv("CRIMINAL_DB_HOST", DB_SECRETS.get("host", "localhost"))
DB_USER = os.getenv("CRIMINAL_DB_USER", DB_SECRETS.get("user", "root"))
DB_PASSWORD = os.getenv("CRIMINAL_DB_PASSWORD", DB_SECRETS.get("password", ""))
DB_NAME = os.getenv("CRIMINAL_DB_NAME", DB_SECRETS.get("name", "criminal_management"))

FIELDS = ["case_id", "criminal_no", "name", "nick_name", "arrest_date", "date_of_crime",
          "address", "age", "occupation", "birth_mark", "crime_type", "father_name",
          "gender", "wanted"]

LABELS = {
    "case_id": "Case ID", "criminal_no": "Criminal No", "name": "Name",
    "nick_name": "Nick Name", "arrest_date": "Arrest Date", "date_of_crime": "Date of Crime",
    "address": "Address", "age": "Age", "occupation": "Occupation",
    "birth_mark": "Birth Mark", "crime_type": "Crime Type", "father_name": "Father Name",
    "gender": "Gender", "wanted": "Wanted",
}


# ------------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------------
def get_connection(database=None):
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=database or DB_NAME, use_pure=True,
    )


def ensure_database_ready():
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, use_pure=True)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cur.execute(f"USE {DB_NAME}")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS criminal (
                case_id VARCHAR(50) PRIMARY KEY,
                criminal_no VARCHAR(50),
                name VARCHAR(100),
                nick_name VARCHAR(100),
                arrest_date VARCHAR(50),
                date_of_crime VARCHAR(50),
                address VARCHAR(255),
                age VARCHAR(10),
                occupation VARCHAR(100),
                birth_mark VARCHAR(100),
                crime_type VARCHAR(100),
                father_name VARCHAR(100),
                gender VARCHAR(10),
                wanted VARCHAR(10)
            )
            """
        )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        st.error(f"Failed to initialize database: {exc}")
        return False


def fetch_all():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM criminal")
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=FIELDS)
    finally:
        conn.close()


def add_record(values):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO criminal VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        tuple(values[f] for f in FIELDS),
    )
    conn.commit()
    conn.close()


def update_record(values):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE criminal SET criminal_no=%s, name=%s, nick_name=%s, arrest_date=%s, date_of_crime=%s,
        address=%s, age=%s, occupation=%s, birth_mark=%s, crime_type=%s, father_name=%s,
        gender=%s, wanted=%s WHERE case_id=%s""",
        (
            values["criminal_no"], values["name"], values["nick_name"], values["arrest_date"],
            values["date_of_crime"], values["address"], values["age"], values["occupation"],
            values["birth_mark"], values["crime_type"], values["father_name"], values["gender"],
            values["wanted"], values["case_id"],
        ),
    )
    conn.commit()
    conn.close()


def delete_record(case_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM criminal WHERE case_id=%s", (case_id,))
    conn.commit()
    conn.close()


def search_records(column, keyword):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM criminal WHERE {column} LIKE %s"
        cursor.execute(query, (f"%{keyword}%",))
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=FIELDS)
    finally:
        conn.close()


def main():
    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    if "db_ready" not in st.session_state:
        st.session_state.db_ready = ensure_database_ready()

    if not st.session_state.db_ready:
        st.stop()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 3rem !important;
            }
            .stApp {
                margin-top: 1rem !important;
                margin-bottom: 1rem !important;
            }
            .header-wrap {
                display: flex;
                align-items: center;
                justify-content: flex-start;
                gap: 16px;
                width: 100%;
                min-height: 86px;
                margin: 0 0 8px 0;
                padding-left: 0;
            }
            .header-logo {
                margin-top: 1rem;
            }
            .header-title-block {
                display: flex;
                flex-direction: column;
                justify-content: center;
                flex: 1;
                min-width: 0;
            }
            .header-title {
                font-size: 2.3rem;
                font-weight: 700;
                line-height: 1.1;
                margin: 0;
                padding: 0;
            }
            .header-subtitle {
                font-size: 1rem;
                color: #666;
                margin-top: 6px;
            }
            .header-time {
                font-size: 1rem;
                font-weight: 600;
                white-space: nowrap;
                color: #1d1d1d;
                margin-left: auto;
                text-align: right;
            }
            .header-title-row {
                display: flex;
                align-items: center;
                flex-wrap: nowrap;
                justify-content: flex-start;
                gap: 10px;
                width: 100%;
                margin-left: 0;
                padding-left: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    header_cols = st.columns([0.7, 7.3])
    with header_cols[0]:
        logo_file = image_path("LOGO2.png")
        if logo_file:
            st.markdown('<div class="header-logo">', unsafe_allow_html=True)
            st.image(logo_file, width=64)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="header-logo"><div style="width: 64px; height: 64px; border-radius: 12px; background: linear-gradient(135deg, #111827, #374151); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.8rem;">🗂️</div></div>', unsafe_allow_html=True)

    with header_cols[1]:
        clock_html = f"""
        <style>
            .header-title-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 100%;
                gap: 10px;
                margin: 0;
                padding: 0;
            }}
            .header-title {{
                font-size: 2.3rem;
                font-weight: 700;
                line-height: 1.1;
                white-space: nowrap;
            }}
            .header-subtitle {{
                font-size: 1rem;
                color: #666;
                margin-top: 6px;
            }}
            .header-time {{
                font-size: 1rem;
                font-weight: 600;
                white-space: nowrap;
                color: #1d1d1d;
                margin-left: auto;
                text-align: right;
            }}
        </style>
        <div class='header-title-row'>
            <div class='header-title'>Criminal Management System</div>
            <div class='header-time' id='live-clock'>{datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}</div>
        </div>
        <div class='header-subtitle'>National Crime Records Console</div>
        <script>
            const clockElement = document.getElementById('live-clock');
            function updateClock() {{
                const now = new Date();
                const pad = (n) => n.toString().padStart(2, '0');
                const value = `${{pad(now.getDate())}}/${{pad(now.getMonth() + 1)}}/${{now.getFullYear()}}  ${{pad(now.getHours())}}:${{pad(now.getMinutes())}}:${{pad(now.getSeconds())}}`;
                clockElement.textContent = value;
            }}
            updateClock();
            setInterval(updateClock, 1000);
        </script>
        """
        components.html(clock_html, height=110)

    # Optional banner row (IMG1.jpg, IMG2.jpg, IMG3.jpg) — shown only if the files exist
    banner_files = [image_path("IMG1.jpg"), image_path("IMG2.jpg"), image_path("IMG3.jpg")]
    banner_files = [f for f in banner_files if f]
    if banner_files:
        b_cols = st.columns(len(banner_files))
        for col, img in zip(b_cols, banner_files):
            col.image(img, width="stretch")

    tab_manage, tab_search, tab_analytics = st.tabs(["Manage Records", "Search", "Analytics"])

    # ------------------------------------------------------------------
    # Tab 1: Manage Records (Add / Update / Delete / Table)
    # ------------------------------------------------------------------
    EMPTY_FORM = {
        "case_id": "", "criminal_no": "", "name": "", "nick_name": "",
        "arrest_date": "", "date_of_crime": "", "address": "", "age": "",
        "occupation": "", "birth_mark": "", "crime_type": "", "father_name": "",
        "gender": "male", "wanted": "yes",
    }

    if "form_values" not in st.session_state:
        st.session_state.form_values = EMPTY_FORM.copy()
    if "loaded_case_id" not in st.session_state:
        st.session_state.loaded_case_id = None

    def reset_form():
        st.session_state.form_values = EMPTY_FORM.copy()
        st.session_state.loaded_case_id = None

    with tab_manage:
        st.subheader("Criminal Information")

        fv = st.session_state.form_values

        with st.form("record_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                case_id = st.text_input("Case ID *", value=fv["case_id"])
                arrest_date = st.text_input("Arrest Date", value=fv["arrest_date"])
                occupation = st.text_input("Occupation", value=fv["occupation"])
                father_name = st.text_input("Father Name", value=fv["father_name"])
            with c2:
                criminal_no = st.text_input("Criminal No *", value=fv["criminal_no"])
                date_of_crime = st.text_input("Date of Crime", value=fv["date_of_crime"])
                birth_mark = st.text_input("Birth Mark", value=fv["birth_mark"])
                gender = st.radio("Gender", ["male", "female"], horizontal=True,
                                   index=["male", "female"].index(fv["gender"]) if fv["gender"] in ["male", "female"] else 0)
            with c3:
                name = st.text_input("Name *", value=fv["name"])
                nick_name = st.text_input("Nick Name", value=fv["nick_name"])
                crime_type = st.text_input("Crime Type", value=fv["crime_type"])
                wanted = st.radio("Wanted", ["yes", "no"], horizontal=True,
                                   index=["yes", "no"].index(fv["wanted"]) if fv["wanted"] in ["yes", "no"] else 0)

            c4, c5 = st.columns(2)
            with c4:
                address = st.text_input("Address", value=fv["address"])
            with c5:
                age = st.text_input("Age", value=fv["age"])

            b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
            save_btn = b1.form_submit_button("💾 Save", width="stretch")
            update_btn = b2.form_submit_button("✏️ Update", width="stretch")
            delete_btn = b3.form_submit_button("🗑️ Delete", width="stretch")
            clear_btn = b4.form_submit_button("🧹 Clear", width="stretch")

        values = {
            "case_id": case_id, "criminal_no": criminal_no, "name": name, "nick_name": nick_name,
            "arrest_date": arrest_date, "date_of_crime": date_of_crime, "address": address,
            "age": age, "occupation": occupation, "birth_mark": birth_mark, "crime_type": crime_type,
            "father_name": father_name, "gender": gender, "wanted": wanted,
        }

        if save_btn:
            if not case_id.strip() or not criminal_no.strip() or not name.strip():
                st.error("Case ID, Criminal No, and Name are required.")
            else:
                try:
                    add_record(values)
                    st.success("✅ Criminal record has been added successfully")
                    reset_form()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        if update_btn:
            if not case_id.strip():
                st.error("Case ID is required to update a record.")
            else:
                try:
                    update_record(values)
                    st.success("✅ Criminal record successfully updated")
                    reset_form()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        if delete_btn:
            if not case_id.strip():
                st.error("Case ID is required to delete a record.")
            else:
                try:
                    delete_record(case_id)
                    st.success("✅ Successfully deleted criminal record")
                    reset_form()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        if clear_btn:
            reset_form()
            st.rerun()

        st.divider()
        st.subheader("Criminal Records")
        st.caption("Click on any row to load its data into the form above.")

        df_all = fetch_all()
        st.caption(f"{len(df_all)} record(s) loaded")

        if not df_all.empty:
            display_df = df_all.rename(columns=LABELS)

            def highlight_wanted(row):
                is_wanted = str(row.get("Wanted", "")).lower() == "yes"
                return ["color: red; font-weight: bold" if is_wanted else "" for _ in row]

            event = st.dataframe(
                display_df.style.apply(highlight_wanted, axis=1),
                width="stretch",
                height=320,
                on_select="rerun",
                selection_mode="single-row",
            )

            selected_rows = event.selection.rows if event and event.selection else []
            if selected_rows:
                picked = df_all.iloc[selected_rows[0]]
                picked_case_id = str(picked["case_id"])
                if picked_case_id != st.session_state.loaded_case_id:
                    st.session_state.form_values = {f: ("" if pd.isna(picked[f]) else str(picked[f])) for f in FIELDS}
                    st.session_state.loaded_case_id = picked_case_id
                    st.rerun()

            csv_buf = io.StringIO()
            df_all.to_csv(csv_buf, index=False)
            st.download_button("⬇️ Export as CSV", csv_buf.getvalue(),
                                file_name="criminal_data_export.csv", mime="text/csv")
        else:
            st.info("No records yet. Add one using the form above.")

    # ------------------------------------------------------------------
    # Tab 2: Search
    # ------------------------------------------------------------------
    with tab_search:
        st.subheader("Search Criminal Record")
        sc1, sc2, sc3 = st.columns([1, 1, 1])
        with sc1:
            search_col = st.selectbox("Search By", ["case_id", "criminal_no", "name", "crime_type", "gender", "wanted"],
                                       format_func=lambda x: LABELS.get(x, x))
        with sc2:
            search_val = st.text_input("Keyword")
        with sc3:
            st.write("")
            st.write("")
            do_search = st.button("🔍 Search", width="stretch")

        if do_search:
            results = search_records(search_col, search_val)
            if results.empty:
                st.warning("No records found")
            else:
                st.dataframe(results.rename(columns=LABELS), width="stretch")

    # ------------------------------------------------------------------
    # Tab 3: Analytics Console
    # ------------------------------------------------------------------
    with tab_analytics:
        raw_data = fetch_all()
        if raw_data.empty:
            st.info("ℹ️ No data available for analytics. Please add criminal records first in the Manage Records tab.")
        else:
            raw_data["age"] = pd.to_numeric(raw_data["age"], errors="coerce")
            
            # ------------------------------------------------------------------
            # Interactive Filter Console
            # ------------------------------------------------------------------
            st.markdown("<div class='section-header-box'>🎛️ Analytics Intelligence Console</div>", unsafe_allow_html=True)
            
            with st.container():
                fc1, fc2, fc3 = st.columns(3)
                
                crime_types = ["All Crimes"] + sorted([str(c) for c in raw_data["crime_type"].dropna().unique() if str(c).strip()])
                with fc1:
                    sel_crime = st.selectbox("Filter Crime Type", crime_types)
                    
                wanted_options = ["All Statuses", "Wanted Only (Yes)", "Not Wanted (No)"]
                with fc2:
                    sel_wanted = st.selectbox("Filter Wanted Status", wanted_options)
                    
                gender_options = ["All Genders"] + sorted([str(g).title() for g in raw_data["gender"].dropna().unique() if str(g).strip()])
                with fc3:
                    sel_gender = st.selectbox("Filter Gender", gender_options)
            
            # Apply Filters
            data = raw_data.copy()
            if sel_crime != "All Crimes":
                data = data[data["crime_type"].astype(str) == sel_crime]
            if sel_wanted == "Wanted Only (Yes)":
                data = data[data["wanted"].astype(str).str.lower() == "yes"]
            elif sel_wanted == "Not Wanted (No)":
                data = data[data["wanted"].astype(str).str.lower() == "no"]
            if sel_gender != "All Genders":
                data = data[data["gender"].astype(str).str.lower() == sel_gender.lower()]

            if data.empty:
                st.warning("⚠️ No records match the selected filter criteria. Try resetting the filters above.")
            else:
                figures = []

                def add_chart(fig):
                    figures.append(fig)

                def style_chart_surface(fig, ax):
                    fig.patch.set_facecolor("#ffffff")
                    fig.patch.set_edgecolor("#e2e8f0")
                    fig.patch.set_linewidth(1.0)
                    ax.set_facecolor("#f8fafc")
                    ax.tick_params(colors="#334155", labelsize=9)
                    for spine in ax.spines.values():
                        spine.set_color("#cbd5e1")
                    if ax.title:
                        ax.title.set_color("#0f172a")
                        ax.title.set_fontsize(11)
                        ax.title.set_fontweight("bold")
                    ax.xaxis.label.set_color("#475569")
                    ax.yaxis.label.set_color("#475569")

                pie_figsize = (4.2, 4.2)

                # ------------------------------------------------------------------
                # KPI Tiles Header
                # ------------------------------------------------------------------
                total_cases = len(data)
                total_raw = len(raw_data)
                wanted_count = int((data["wanted"].astype(str).str.lower() == "yes").sum())
                wanted_pct = (wanted_count / total_cases * 100) if total_cases > 0 else 0
                
                most_common_crime = data["crime_type"].mode()[0] if not data["crime_type"].mode().empty else "N/A"
                top_crime_count = data["crime_type"].value_counts().iloc[0] if not data["crime_type"].value_counts().empty else 0
                
                avg_age = data["age"].mean()
                avg_age_str = f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "N/A"

                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                with kpi1:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-title">📊 Total Cases</div>
                            <div class="metric-value">{total_cases:,}</div>
                            <div class="metric-subtext">out of {total_raw:,} total database records</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with kpi2:
                    st.markdown(
                        f"""
                        <div class="metric-card red">
                            <div class="metric-title">🚨 Wanted Criminals</div>
                            <div class="metric-value">{wanted_count:,}</div>
                            <div class="metric-subtext">{wanted_pct:.1f}% high risk suspects</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with kpi3:
                    st.markdown(
                        f"""
                        <div class="metric-card purple">
                            <div class="metric-title">📈 Top Crime Category</div>
                            <div class="metric-value" style="font-size: 1.35rem; font-weight: 700;">{most_common_crime}</div>
                            <div class="metric-subtext">{top_crime_count} registered case(s)</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with kpi4:
                    st.markdown(
                        f"""
                        <div class="metric-card green">
                            <div class="metric-title">👥 Avg Suspect Age</div>
                            <div class="metric-value">{avg_age_str}</div>
                            <div class="metric-subtext">demographic age center</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                # ------------------------------------------------------------------
                # Section 1: Crime Analysis
                # ------------------------------------------------------------------
                st.markdown("<div class='section-header-box'>📊 Crime Type & Pattern Analysis</div>", unsafe_allow_html=True)
                crime_col1, crime_col2 = st.columns([1.6, 1])
                
                with crime_col1:
                    crime_counts = data["crime_type"].value_counts().head(8)
                    fig, ax = plt.subplots(figsize=(8, 4.6))
                    palette = ["#3b82f6", "#06b6d4", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b", "#ef4444", "#6366f1"]
                    colors = [palette[i % len(palette)] for i in range(len(crime_counts))]
                    bars = ax.bar(range(len(crime_counts)), crime_counts.values, color=colors, edgecolor="#ffffff", linewidth=1.2, width=0.6)
                    ax.set_xticks(range(len(crime_counts)))
                    ax.set_xticklabels(crime_counts.index, rotation=30, ha="right", fontweight="bold")
                    ax.set_title("Top Registered Crime Categories")
                    ax.set_xlabel("Crime Type")
                    ax.set_ylabel("Number of Cases")
                    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                    ax.grid(axis="y", alpha=0.3, linestyle="--")
                    for bar in bars:
                        h = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05, f"{int(h)}", ha="center", va="bottom", fontweight="bold", color="#1e293b")
                    style_chart_surface(fig, ax)
                    fig.tight_layout()
                    st.pyplot(fig)
                    add_chart(fig)

                with crime_col2:
                    top_crimes = crime_counts
                    fig, ax = plt.subplots(figsize=pie_figsize)
                    wedges, texts, autotexts = ax.pie(
                        top_crimes.values,
                        labels=top_crimes.index,
                        autopct="%1.1f%%",
                        startangle=90,
                        pctdistance=0.72,
                        colors=colors,
                        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
                    )
                    plt.setp(autotexts, size=9, weight="bold", color="white")
                    plt.setp(texts, size=8.5, weight="semibold")
                    ax.set_title("Crime Share Breakdown (%)")
                    style_chart_surface(fig, ax)
                    fig.tight_layout()
                    st.pyplot(fig, width=330)
                    add_chart(fig)

                # ------------------------------------------------------------------
                # Section 2: Demographic Analysis
                # ------------------------------------------------------------------
                st.markdown("<div class='section-header-box'>🧬 Demographic & Age Distribution</div>", unsafe_allow_html=True)
                demo_col1, demo_col2 = st.columns([1.6, 1])
                
                with demo_col1:
                    bins = [0, 18, 25, 35, 45, 55, 65, 100]
                    age_labels = ["Under 18", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
                    valid_ages = data["age"].dropna()
                    if not valid_ages.empty:
                        age_groups = pd.cut(valid_ages, bins=bins, labels=age_labels, right=False)
                        age_group_counts = age_groups.value_counts().sort_index()
                        fig, ax = plt.subplots(figsize=(8, 4.4))
                        bar_colors = ["#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#1e3a8a", "#172554"]
                        bars = ax.bar(
                            age_group_counts.index,
                            age_group_counts.values,
                            color=bar_colors[:len(age_group_counts)],
                            edgecolor="white",
                            linewidth=1.2,
                            width=0.55,
                        )
                        for bar in bars:
                            h = bar.get_height()
                            if h > 0:
                                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05, f"{int(h)}", ha="center", va="bottom", fontweight="bold", color="#1e293b")
                        ax.set_title("Criminal Age Group Breakdown")
                        ax.set_xlabel("Age Group")
                        ax.set_ylabel("Suspect Count")
                        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                        ax.grid(axis="y", alpha=0.3, linestyle="--")
                        style_chart_surface(fig, ax)
                        fig.tight_layout()
                        st.pyplot(fig)
                        add_chart(fig)
                    else:
                        st.info("No age data available for current filter.")

                with demo_col2:
                    gender_counts = data["gender"].fillna("unknown").astype(str).str.title().value_counts()
                    fig, ax = plt.subplots(figsize=pie_figsize)
                    gender_colors_map = {"Male": "#3b82f6", "Female": "#ec4899", "Unknown": "#94a3b8"}
                    g_colors = [gender_colors_map.get(g, "#8b5cf6") for g in gender_counts.index]
                    wedges, texts, autotexts = ax.pie(
                        gender_counts.values,
                        labels=gender_counts.index,
                        autopct="%1.1f%%",
                        startangle=90,
                        pctdistance=0.72,
                        colors=g_colors,
                        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
                    )
                    plt.setp(autotexts, size=9, weight="bold", color="white")
                    plt.setp(texts, size=9, weight="semibold")
                    ax.set_title("Gender Ratio")
                    style_chart_surface(fig, ax)
                    fig.tight_layout()
                    st.pyplot(fig, width=330)
                    add_chart(fig)

                # ------------------------------------------------------------------
                # Section 3: Risk Profile & Occupations
                # ------------------------------------------------------------------
                st.markdown("<div class='section-header-box'>🚩 Risk Profiles & Occupations</div>", unsafe_allow_html=True)
                status_col1, status_col2 = st.columns([1, 1.4])
                
                with status_col1:
                    wanted_counts = data["wanted"].astype(str).str.lower().value_counts()
                    labels_map = {"yes": "Wanted (Active)", "no": "Not Wanted (Captured)"}
                    colors_map = {"yes": "#ef4444", "no": "#10b981"}
                    display_labels = [labels_map.get(x, x.title()) for x in wanted_counts.index]
                    
                    fig, ax = plt.subplots(figsize=(5.8, 4.4))
                    bars = ax.bar(
                        display_labels,
                        wanted_counts.values,
                        color=[colors_map.get(x, "#64748b") for x in wanted_counts.index],
                        edgecolor="white",
                        linewidth=1.2,
                        width=0.45,
                    )
                    for bar in bars:
                        h = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05, f"{int(h)}", ha="center", va="bottom", fontweight="bold", color="#1e293b")
                    ax.set_title("Wanted vs Captured Status")
                    ax.set_xlabel("Status")
                    ax.set_ylabel("Number of Criminals")
                    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                    ax.grid(axis="y", alpha=0.3, linestyle="--")
                    style_chart_surface(fig, ax)
                    fig.tight_layout()
                    st.pyplot(fig)
                    add_chart(fig)

                with status_col2:
                    if data["occupation"].notna().any():
                        occ_counts = data["occupation"].value_counts().head(10)
                        fig, ax = plt.subplots(figsize=(7, 4.4))
                        colors_occ = plt.cm.Blues(np.linspace(0.4, 0.9, len(occ_counts)))
                        bars = ax.barh(
                            occ_counts.index[::-1],
                            occ_counts.values[::-1],
                            color=colors_occ[::-1],
                            edgecolor="white",
                            linewidth=1.2,
                            height=0.6,
                        )
                        for bar in bars:
                            w = bar.get_width()
                            ax.text(w + 0.05, bar.get_y() + bar.get_height() / 2, f"{int(w)}", ha="left", va="center", fontweight="bold", color="#1e293b")
                        ax.set_title("Top Suspect Occupations")
                        ax.set_xlabel("Number of Criminals")
                        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                        ax.grid(axis="x", alpha=0.3, linestyle="--")
                        style_chart_surface(fig, ax)
                        fig.tight_layout()
                        st.pyplot(fig)
                        add_chart(fig)
                    else:
                        st.info("No occupation data available for current filter selection.")

                # ------------------------------------------------------------------
                # Section 4: Cross Analysis (Wanted Status by Gender)
                # ------------------------------------------------------------------
                st.markdown("<div class='section-header-box'>⚔️ Cross-Analysis: Wanted Status by Gender</div>", unsafe_allow_html=True)
                gender_wanted = pd.crosstab(data["gender"].fillna("unknown").astype(str).str.title(), data["wanted"].fillna("no").astype(str).str.lower())
                gender_wanted = gender_wanted.rename(columns={"yes": "Wanted", "no": "Not Wanted"})
                
                fig, ax = plt.subplots(figsize=(9.5, 4.0))
                gender_wanted.plot(kind="bar", ax=ax, color=["#10b981", "#ef4444"], edgecolor="white", width=0.5)
                ax.set_title("Wanted Status Cross-Tabulation by Gender")
                ax.set_xlabel("Gender")
                ax.set_ylabel("Number of Cases")
                ax.legend(title="Status", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1")
                ax.grid(axis="y", alpha=0.3, linestyle="--")
                plt.xticks(rotation=0, fontweight="bold")
                style_chart_surface(fig, ax)
                fig.tight_layout()
                st.pyplot(fig)
                add_chart(fig)

                # ------------------------------------------------------------------
                # Section 5: Executive Statistical Summary Matrix
                # ------------------------------------------------------------------
                st.markdown("<div class='section-header-box'>📋 Detailed Statistical Metrics</div>", unsafe_allow_html=True)
                
                median_age = data["age"].median()
                std_age = data["age"].std()
                male_count = int((data["gender"].astype(str).str.lower() == "male").sum())
                female_count = int((data["gender"].astype(str).str.lower() == "female").sum())
                male_pct = (male_count / total_cases * 100) if total_cases else 0
                female_pct = (female_count / total_cases * 100) if total_cases else 0
                youngest = data["age"].min()
                oldest = data["age"].max()
                age_range = (oldest - youngest) if pd.notna(oldest) and pd.notna(youngest) else np.nan

                summary_rows = [
                    [
                        ("Active Data Subset", f"{total_cases:,}", f"{total_cases/total_raw*100:.1f}% of DB"),
                        ("Average Age", f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "N/A"),
                        ("Median Age", f"{median_age:.1f} yrs" if pd.notna(median_age) else "N/A"),
                        ("Age Std Deviation", f"{std_age:.1f} yrs" if pd.notna(std_age) else "N/A"),
                    ],
                    [
                        ("Top Crime Type", f"{most_common_crime}", f"{top_crime_count} case(s)"),
                        ("Active Wanted", f"{wanted_count:,}", f"{wanted_pct:.1f}% risk"),
                        ("Male Suspects", f"{male_count:,}", f"{male_pct:.1f}%"),
                        ("Female Suspects", f"{female_count:,}", f"{female_pct:.1f}%"),
                    ],
                    [
                        ("Youngest Suspect", f"{youngest:.0f} yrs" if pd.notna(youngest) else "N/A"),
                        ("Oldest Suspect", f"{oldest:.0f} yrs" if pd.notna(oldest) else "N/A"),
                        ("Age Span", f"{age_range:.0f} yrs" if pd.notna(age_range) else "N/A"),
                        ("Total DB Capacity", f"{total_raw:,} records"),
                    ],
                ]

                for row in summary_rows:
                    cols = st.columns(4)
                    for col, item in zip(cols, row):
                        with col:
                            st.metric(label=item[0], value=item[1], delta=item[2] if len(item) > 2 else None)

                # ------------------------------------------------------------------
                # Section 6: Report Export Hub
                # ------------------------------------------------------------------
                st.markdown("<div class='section-header-box'>📥 Analytics Report Export Hub</div>", unsafe_allow_html=True)
                exp1, exp2 = st.columns(2)

                with exp1:
                    st.markdown("<div class='export-card'><h4>📄 High-Res PDF Executive Report</h4><p style='color:#64748b; font-size:0.9rem;'>Download all high-resolution charts bundled into a print-ready PDF document.</p></div>", unsafe_allow_html=True)
                    pdf_buf = io.BytesIO()
                    with PdfPages(pdf_buf) as pdf:
                        for f in figures:
                            pdf.savefig(f, bbox_inches="tight")
                    pdf_buf.seek(0)
                    st.download_button(
                        "📄 Download Analytics PDF Report",
                        data=pdf_buf,
                        file_name="criminal_analytics_executive_report.pdf",
                        mime="application/pdf",
                        width="stretch",
                    )

                with exp2:
                    st.markdown("<div class='export-card'><h4>🖼️ Image Bundle (ZIP Archive)</h4><p style='color:#64748b; font-size:0.9rem;'>Export raw chart images in high 200 DPI PNG format for presentations.</p></div>", unsafe_allow_html=True)
                    zip_buf = io.BytesIO()
                    chart_names = [
                        "crime_type_distribution.png",
                        "crime_type_donut.png",
                        "age_distribution.png",
                        "gender_ratio.png",
                        "wanted_status.png",
                        "top_occupations.png",
                        "wanted_by_gender.png",
                    ]
                    with zipfile.ZipFile(zip_buf, "w") as zf:
                        for f, name in zip(figures, chart_names):
                            img_buf = io.BytesIO()
                            f.savefig(img_buf, format="png", dpi=200, bbox_inches="tight")
                            zf.writestr(name, img_buf.getvalue())
                    zip_buf.seek(0)
                    st.download_button(
                        "🖼️ Download PNG Charts ZIP",
                        data=zip_buf,
                        file_name="criminal_analytics_charts.zip",
                        mime="application/zip",
                        width="stretch",
                    )


if __name__ == "__main__":
    main()

