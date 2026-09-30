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
    # Tab 3: Analytics
    # ------------------------------------------------------------------
    with tab_analytics:
        data = fetch_all()
        if data.empty:
            st.info("No data available for charts. Add some records first.")
        else:
            data["age"] = pd.to_numeric(data["age"], errors="coerce")
            figures = []

            def add_chart(fig):
                figures.append(fig)

            def style_chart_surface(fig, ax):
                fig.patch.set_facecolor("#f1f6f8")
                fig.patch.set_edgecolor("#8aa2ad")
                fig.patch.set_linewidth(1.5)
                fig.patch.set_path_effects([
                    patheffects.SimplePatchShadow(offset=(3, -3), alpha=0.18),
                    patheffects.Normal(),
                ])
                ax.set_facecolor("#fbfdfe")

            pie_figsize = (4, 4)

            st.subheader("Crime Analysis")
            crime_col1, crime_col2 = st.columns([1.6, 1])
            with crime_col1:
                crime_counts = data["crime_type"].value_counts().head(8)
                fig, ax = plt.subplots(figsize=(8, 4.6))
                colors = plt.cm.Set3(np.linspace(0, 1, len(crime_counts)))
                bars = ax.bar(range(len(crime_counts)), crime_counts.values, color=colors, edgecolor="black")
                ax.set_xticks(range(len(crime_counts)))
                ax.set_xticklabels(crime_counts.index, rotation=45, ha="right")
                ax.set_title("Crime Type Distribution")
                ax.set_xlabel("Crime Type")
                ax.set_ylabel("Number of Cases")
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                ax.grid(axis="y", alpha=0.3, linestyle="--")
                for bar in bars:
                    h = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontweight="bold")
                style_chart_surface(fig, ax)
                fig.tight_layout()
                st.pyplot(fig)
                add_chart(fig)

            with crime_col2:
                top_crimes = crime_counts
                fig, ax = plt.subplots(figsize=pie_figsize)
                ax.pie(
                    top_crimes.values,
                    labels=top_crimes.index,
                    autopct="%1.1f%%",
                    startangle=90,
                    radius=0.72,
                    labeldistance=1.05,
                    pctdistance=0.68,
                    colors=plt.cm.Paired(np.linspace(0, 1, len(top_crimes))),
                )
                ax.set_title("Top Crime Types (%)")
                style_chart_surface(fig, ax)
                fig.tight_layout()
                st.pyplot(fig, width=320)
                add_chart(fig)

            st.subheader("Demographic Analysis")
            demo_col1, demo_col2 = st.columns(2)
            with demo_col1:
                bins = [0, 18, 25, 35, 45, 55, 65, 100]
                age_labels = ["Under 18", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
                age_groups = pd.cut(data["age"].dropna(), bins=bins, labels=age_labels, right=False)
                age_group_counts = age_groups.value_counts().sort_index()
                fig, ax = plt.subplots(figsize=(7, 4.4))
                bars = ax.bar(
                    age_group_counts.index,
                    age_group_counts.values,
                    color=plt.cm.Blues(np.linspace(0.4, 0.8, len(age_group_counts))),
                    edgecolor="black",
                )
                for bar in bars:
                    h = bar.get_height()
                    if h > 0:
                        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontweight="bold")
                ax.set_title("Age Distribution")
                ax.set_xlabel("Age Group")
                ax.set_ylabel("Number of Criminals")
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                ax.grid(axis="y", alpha=0.3, linestyle="--")
                style_chart_surface(fig, ax)
                fig.tight_layout()
                st.pyplot(fig)
                add_chart(fig)

            with demo_col2:
                gender_counts = data["gender"].fillna("unknown").value_counts()
                fig, ax = plt.subplots(figsize=pie_figsize)
                ax.pie(
                    gender_counts.values,
                    labels=[g.title() for g in gender_counts.index],
                    autopct="%1.1f%%",
                    startangle=90,
                    radius=0.72,
                    labeldistance=1.05,
                    pctdistance=0.68,
                    colors=["#4ECDC4", "#FF6B6B", "#A78BFA"],
                )
                ax.set_title("Gender Distribution")
                style_chart_surface(fig, ax)
                fig.tight_layout()
                st.pyplot(fig, width=320)
                add_chart(fig)

            st.subheader("Wanted & Occupation")
            status_col1, status_col2 = st.columns([1.1, 1.3])
            with status_col1:
                wanted_counts = data["wanted"].value_counts()
                colors_map = {"yes": "#FF6B6B", "no": "#4ECDC4"}
                fig, ax = plt.subplots(figsize=(5.8, 4.2))
                bars = ax.bar(
                    wanted_counts.index,
                    wanted_counts.values,
                    color=[colors_map.get(x, "#888") for x in wanted_counts.index],
                    edgecolor="black",
                    width=0.5,
                )
                for bar in bars:
                    h = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontweight="bold")
                ax.set_title("Wanted Status")
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
                    fig, ax = plt.subplots(figsize=(6.2, 4.4))
                    ax.barh(
                        occ_counts.index[::-1],
                        occ_counts.values[::-1],
                        color=plt.cm.tab20c(np.linspace(0, 1, len(occ_counts))),
                        edgecolor="black",
                    )
                    ax.set_title("Top 10 Occupations")
                    ax.set_xlabel("Number of Criminals")
                    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                    ax.grid(axis="x", alpha=0.3, linestyle="--")
                    style_chart_surface(fig, ax)
                    fig.tight_layout()
                    st.pyplot(fig)
                    add_chart(fig)
                else:
                    st.info("No occupation data available")

            st.subheader("Wanted Status by Gender")
            gender_wanted = pd.crosstab(data["gender"].fillna("unknown"), data["wanted"].fillna("no"))
            fig, ax = plt.subplots(figsize=(9, 3.9))
            gender_wanted.plot(kind="bar", ax=ax, color=["#FF6B6B", "#4ECDC4"], edgecolor="black", width=0.6)
            ax.set_title("Wanted Status by Gender")
            ax.set_xlabel("Gender")
            ax.set_ylabel("Cases")
            ax.legend(title="Wanted")
            ax.grid(axis="y", alpha=0.3, linestyle="--")
            plt.xticks(rotation=0)
            style_chart_surface(fig, ax)
            fig.tight_layout()
            st.pyplot(fig)
            add_chart(fig)

            st.subheader("Statistical Summary")
            total = len(data)
            avg_age = data["age"].mean()
            median_age = data["age"].median()
            std_age = data["age"].std()
            most_common_crime = data["crime_type"].mode()[0] if not data["crime_type"].mode().empty else "N/A"
            crime_frequency = data["crime_type"].value_counts().iloc[0] if not data["crime_type"].value_counts().empty else 0
            wanted_count = int((data["wanted"] == "yes").sum())
            wanted_percentage = (wanted_count / total * 100) if total else 0
            male_count = int((data["gender"] == "male").sum())
            female_count = int((data["gender"] == "female").sum())
            male_percentage = (male_count / total * 100) if total else 0
            female_percentage = (female_count / total * 100) if total else 0
            youngest = data["age"].min()
            oldest = data["age"].max()
            age_range = (oldest - youngest) if pd.notna(oldest) and pd.notna(youngest) else np.nan

            summary_rows = [
                [
                    ("Total Cases", f"{total:,}"),
                    ("Average Age", f"{avg_age:.1f} yrs" if total else "N/A"),
                    ("Median Age", f"{median_age:.1f} yrs" if total else "N/A"),
                    ("Age Std Dev", f"{std_age:.1f} yrs" if total else "N/A"),
                ],
                [
                    ("Most Common Crime", f"{most_common_crime}", f"{crime_frequency} case(s)"),
                    ("Wanted Criminals", f"{wanted_count:,}", f"{wanted_percentage:.1f}%"),
                    ("Male", f"{male_count:,}", f"{male_percentage:.1f}%"),
                    ("Female", f"{female_count:,}", f"{female_percentage:.1f}%"),
                ],
                [
                    ("Youngest Criminal", f"{youngest:.0f} yrs" if pd.notna(youngest) else "N/A"),
                    ("Oldest Criminal", f"{oldest:.0f} yrs" if pd.notna(oldest) else "N/A"),
                    ("Age Range", f"{age_range:.0f} yrs" if pd.notna(age_range) else "N/A"),
                    ("Data Points", f"{len(data)}"),
                ],
            ]

            for row in summary_rows:
                cols = st.columns(4)
                for col, item in zip(cols, row):
                    if len(item) == 2:
                        col.metric(item[0], item[1])
                    else:
                        col.metric(item[0], item[1], item[2])

            overview_labels = ["Male", "Female", "Wanted", "Not Wanted"]
            overview_values = [male_count, female_count, wanted_count, total - wanted_count]
            overview_data = [(lbl, val) for lbl, val in zip(overview_labels, overview_values) if val > 0]
            if overview_data:
                labels, values = zip(*overview_data)
                fig, ax = plt.subplots(figsize=pie_figsize)
                ax.pie(
                    values,
                    labels=labels,
                    autopct="%1.1f%%",
                    startangle=90,
                    radius=0.72,
                    labeldistance=1.05,
                    pctdistance=0.68,
                    colors=["#66B2FF", "#FF9999", "#FF6B6B", "#4ECDC4"][: len(values)],
                )
                ax.set_title("Quick Overview")
                style_chart_surface(fig, ax)
                fig.tight_layout()
                st.pyplot(fig, width=320)
                add_chart(fig)

            st.divider()
            st.subheader("Export Charts")
            exp1, exp2 = st.columns(2)

            with exp1:
                pdf_buf = io.BytesIO()
                with PdfPages(pdf_buf) as pdf:
                    for f in figures:
                        pdf.savefig(f, bbox_inches="tight")
                pdf_buf.seek(0)
                st.download_button(
                    "📄 Export as PDF",
                    data=pdf_buf,
                    file_name="criminal_analytics_report.pdf",
                    mime="application/pdf",
                    width="stretch",
                )

            with exp2:
                zip_buf = io.BytesIO()
                chart_names = [
                    "crime_type_distribution.png",
                    "crime_type_pie.png",
                    "age_distribution.png",
                    "gender_distribution.png",
                    "wanted_status.png",
                    "top_occupations.png",
                    "wanted_by_gender.png",
                    "quick_overview.png",
                ]
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    for f, name in zip(figures, chart_names):
                        img_buf = io.BytesIO()
                        f.savefig(img_buf, format="png", dpi=200, bbox_inches="tight")
                        zf.writestr(name, img_buf.getvalue())
                zip_buf.seek(0)
                st.download_button(
                    "🖼️ Export Images (ZIP)",
                    data=zip_buf,
                    file_name="criminal_analytics_charts.zip",
                    mime="application/zip",
                    width="stretch",
                )


if __name__ == "__main__":
    main()
