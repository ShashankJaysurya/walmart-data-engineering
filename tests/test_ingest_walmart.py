import tempfile
import unittest
from pathlib import Path

from scripts.ingest_walmart import _identifier, validate_csv


class ValidateCsvTests(unittest.TestCase):
    def test_accepts_required_columns_and_counts_rows(self):
        content = (
            "Store,Date,Weekly_Sales,Holiday_Flag,Temperature,Fuel_Price,CPI,Unemployment\n"
            "1,2/5/2010,1643690.9,0,42.31,2.572,211.096,8.106\n"
            "1,2/12/2010,1641957.44,1,38.51,2.548,211.242,8.106\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "sales.csv"
            csv_path.write_text(content, encoding="utf-8")
            self.assertEqual(validate_csv(csv_path), 2)

    def test_rejects_missing_required_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "sales.csv"
            csv_path.write_text("Store,Date\n1,2/5/2010\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "required names and order"):
                validate_csv(csv_path)

    def test_rejects_empty_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "sales.csv"
            csv_path.write_text(
                "Store,Date,Weekly_Sales,Holiday_Flag,Temperature,Fuel_Price,CPI,Unemployment\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "no data rows"):
                validate_csv(csv_path)

    def test_rejects_unsafe_sql_identifiers(self):
        with self.assertRaisesRegex(ValueError, "simple SQL identifier"):
            _identifier("sales; DROP TABLE users", "catalog")


if __name__ == "__main__":
    unittest.main()
