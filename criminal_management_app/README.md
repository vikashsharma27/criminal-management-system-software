# Criminal Management System

A Streamlit dashboard for managing criminal records, searching stored records,
and reviewing crime and demographic analytics. MySQL stores application data.

> **Data warning:** Criminal-record information is highly sensitive. This sample
> application does not provide user authentication, role-based authorization,
> audit logging, or production security controls. Use synthetic data for demos;
> do not expose it to the public internet or use it for operational records
> without a formal security and privacy review.

## Features

- Create, update, search, and delete records using a MySQL database.
- Browse records and export them as CSV.
- View crime-type, age, gender, wanted-status, occupation, and summary charts.
- Export analytics charts as PDF or image files.
- Initialize the database and `criminal` table automatically on first run.

## Project layout

```text
.
├── README.md
├── tests/
│   └── test_app_smoke.py
└── criminal_management_app/
    ├── app.py
    ├── requirements.txt
    ├── run.bat
    ├── run.sh
    ├── IMAGE/
    └── .streamlit/
        ├── config.toml
        └── secrets.example.toml
```

## Requirements

- Python 3.9 or newer
- MySQL Server reachable from the machine running Streamlit

Install the Python dependencies from the application directory:

```bash
cd criminal_management_app
python -m pip install -r requirements.txt
```

## Database configuration

Keep database credentials out of source control. Configure them using either
Streamlit secrets or environment variables.

For Streamlit secrets, copy
`criminal_management_app/.streamlit/secrets.example.toml` to
`criminal_management_app/.streamlit/secrets.toml`, then set your local MySQL
values in that ignored file:

```toml
[database]
host = "localhost"
user = "root"
password = "your-local-mysql-password"
name = "criminal_management"
```

Alternatively, set `CRIMINAL_DB_HOST`, `CRIMINAL_DB_USER`,
`CRIMINAL_DB_PASSWORD`, and `CRIMINAL_DB_NAME` in the environment. Environment
variables take precedence over Streamlit secrets. The database user needs
permission to create the database and table on first launch, or an administrator
must create them in advance.

## Run the app

From the application directory:

```bash
python -m streamlit run app.py
```

Then open `http://localhost:8501`. On Windows, `run.bat` installs dependencies
and starts Streamlit. On macOS or Linux, run `./run.sh`.

## Tests

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

The MySQL smoke test is skipped when no database password is configured. To run
it, configure credentials and make sure MySQL and the application database are
available.

## Images

Optional banner and logo images belong in `criminal_management_app/IMAGE/`.
Supported filenames include `LOGO2.png` and `IMG1.jpg` through `IMG4.jpg`.
Missing optional images are ignored.
