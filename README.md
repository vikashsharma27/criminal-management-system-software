# 🗂️ Criminal Management System Software

[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

An executive **National Crime Records Console** and data analytics dashboard built with **Python**, **Streamlit**, and **MySQL**. This application provides an end-to-end management workflow for law enforcement records, search queries, demographic intelligence profiling, and report exports.

---

## 🚀 Features

- **📑 Manage Records (CRUD):** Add, update, delete, and browse criminal records with instant table selection and auto-filling form inputs.
- **🔍 Advanced Search Console:** Filter records by Case ID, Criminal No, Name, Crime Type, Gender, or Wanted Status with keyword matching.
- **🎛️ Analytics Intelligence Console:**
  - Interactive multi-parameter filters (Crime Type, Wanted Status, Gender).
  - High-executive KPI metric tiles (Total Cases, Active Wanted Suspects %, Primary Crime Type, Average Age).
  - High-resolution data visualizations: Donut charts, age distribution bar charts, gender ratios, wanted status cross-tabulations, and top occupations.
- **📥 Data & Report Export Hub:** Export dataset to CSV, export full analytical charts to a print-ready PDF executive report, or download a 200 DPI PNG chart image bundle (ZIP archive).
- **🗄️ Automated Database Provisioning:** Automatically initializes the `criminal_management` database and `criminal` table on startup.

---

## 🛠️ Project Structure

```text
.
├── README.md                           # Main repository documentation
├── .gitignore                          # Git ignore rules (protects secrets.toml)
├── tests/                              # Automated test suite
│   └── test_app_smoke.py              # MySQL connection & schema smoke test
└── criminal_management_app/
    ├── app.py                          # Streamlit application core code
    ├── requirements.txt                # Python dependencies
    ├── run.bat                         # One-click Windows launch script
    ├── run.sh                          # Linux / macOS launch script
    ├── README.md                       # Application subfolder docs
    ├── IMAGE/                          # Logo & header images
    │   └── LOGO2.png
    └── .streamlit/                     # Streamlit configuration
        ├── config.toml
        └── secrets.example.toml        # Secrets template
```

---

## 💻 Installation & Local Setup

### 1. Prerequisites
- **Python 3.9+** installed on your system.
- **MySQL Server 8.0+** running locally or on a accessible network server.

### 2. Clone Repository
```bash
git clone https://github.com/vikashsharma27/criminal-management-system-software.git
cd criminal-management-system-software
```

### 3. Install Dependencies
```bash
pip install -r criminal_management_app/requirements.txt
```

### 4. Database Configuration
Create a `.streamlit/secrets.toml` file inside the `criminal_management_app/.streamlit/` directory:

```toml
[database]
host = "localhost"
user = "root"
password = "YOUR_LOCAL_MYSQL_PASSWORD"
name = "criminal_management"
```

*Alternatively, set environment variables:* `CRIMINAL_DB_HOST`, `CRIMINAL_DB_USER`, `CRIMINAL_DB_PASSWORD`, and `CRIMINAL_DB_NAME`.

---

## 🚀 Running the Application

### Windows (One-Click)
Double-click `criminal_management_app/run.bat` or run:
```cmd
cd criminal_management_app
run.bat
```

### Command Line (All Platforms)
```bash
cd criminal_management_app
python -m streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🌐 Online Deployment (Streamlit Community Cloud)

You can host this project online for **free** on Streamlit Community Cloud:

1. Push your code to GitHub: `https://github.com/vikashsharma27/criminal-management-system-software`
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
3. Click **"New App"** and configure:
   - **Repository:** `vikashsharma27/criminal-management-system-software`
   - **Branch:** `main`
   - **Main file path:** `criminal_management_app/app.py`
4. Under **"Advanced settings" -> "Secrets"**, enter your cloud MySQL database credentials:
   ```toml
   [database]
   host = "your-cloud-mysql-host.com"
   user = "your_username"
   password = "your_password"
   name = "criminal_management"
   ```
5. Click **"Deploy!"**

---

## 🧪 Running Automated Tests

Run the unittest suite from the repository root:
```bash
python -m unittest discover -s tests -v
```

---

## 🛡️ Security Disclaimer
> **Important:** Criminal record data is sensitive. This application is intended for educational, demonstration, and administrative sample purposes. Ensure proper authentication, SSL encryption, and access controls before deploying to production environments with real data.
