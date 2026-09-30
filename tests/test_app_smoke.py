import sys
import unittest
import warnings
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parents[1] / "criminal_management_app"
sys.path.insert(0, str(APP_DIR))

import app


class AppSmokeTest(unittest.TestCase):
    def test_fetch_all_uses_clean_mysql_dataframe(self):
        if not app.DB_PASSWORD:
            self.skipTest("Configure MySQL credentials before running database smoke tests")

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "error",
                message="pandas only supports SQLAlchemy connectable.*",
                category=UserWarning,
            )
            df = app.fetch_all()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("case_id", df.columns)


if __name__ == "__main__":
    unittest.main()
