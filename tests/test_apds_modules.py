"""APDS Python modules: pipelines, generators and streaming solutions."""

import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_module(name: str, rel_path: str):
    """Import an APDS module under a unique name (avoids utils collisions)."""
    mod_name = f"apds_{name}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


helpers = load_module("02_helpers", "APDS/02_Sales_Inventory_Pipeline/utils/helpers.py")
product_mod = load_module("02_product", "APDS/02_Sales_Inventory_Pipeline/utils/product.py")
students_mod = load_module("03_students", "APDS/03_Student_Simulation_Analytics/students.py")
analysis_mod = load_module("03_analysis", "APDS/03_Student_Simulation_Analytics/analysis.py")
gen_mod = load_module("04_generate", "APDS/04_One_Million_Record_Streaming/generate_dataset.py")
stream_mod = load_module("04_stream", "APDS/04_One_Million_Record_Streaming/streaming_solutions.py")
utils07 = load_module("07_utils", "APDS/07_Monthly_Sales_Forecasting/utils.py")


# ---------------------------------------------------------------------------
# 02_Sales_Inventory_Pipeline
# ---------------------------------------------------------------------------
class TestCleanLines:
    def test_loop_and_comprehension_agree(self):
        lines = ["  Laptop,1000,3  \n", "\n", "   \n", "Phone,500,5\n", "Tablet,700,2\n"]
        assert helpers.clean_lines_loop(lines) == helpers.clean_lines(lines)

    def test_strips_whitespace_and_drops_empty(self):
        lines = ["  a  \n", "\n", "b\n", "   \n"]
        assert helpers.clean_lines(lines) == ["a", "b"]

    def test_empty_input(self):
        assert helpers.clean_lines([]) == []
        assert helpers.clean_lines(["\n", "  \n"]) == []


class TestParseProducts:
    def test_valid_rows(self):
        rows = ["Laptop,1000.0,3", "Phone, 500 , 5"]
        out = helpers.parse_products(rows)
        assert out == [("Laptop", 1000.0, 3), ("Phone", 500.0, 5)]

    def test_malformed_field_count_is_skipped(self):
        out = helpers.parse_products(["OnlyOneField", "a,b", "a,b,c,d", "Laptop,1000,3"])
        assert out == [("Laptop", 1000.0, 3)]

    def test_invalid_number_is_skipped(self):
        out = helpers.parse_products(['"Corrupted Row",InvalidPrice,10', "Tablet,700,2"])
        assert out == [("Tablet", 700.0, 2)]

    def test_quotes_stripped_from_names(self):
        out = helpers.parse_products(['"Laptop",1000,3'])
        assert out[0][0] == "Laptop"


class TestProduct:
    def test_total_value(self):
        p = product_mod.Product("Laptop", 1000.0, 3)
        assert p.total_value() == 3000.0

    def test_str_contains_fields(self):
        p = product_mod.Product("Phone", 500.0, 5)
        s = str(p)
        assert "Phone" in s and "500" in s and "5" in s

    def test_zero_quantity(self):
        assert product_mod.Product("X", 10.0, 0).total_value() == 0.0


# ---------------------------------------------------------------------------
# 03_Student_Simulation_Analytics
# ---------------------------------------------------------------------------
class TestGenerateStudents:
    def test_count_and_ids(self):
        cohort = students_mod.generate_students(num_students=7, seed=101)
        assert len(cohort) == 7
        assert [s["student_id"] for s in cohort] == [f"STU_{i:03d}" for i in range(1, 8)]

    def test_seeded_determinism(self):
        a = students_mod.generate_students(num_students=5, seed=101)
        b = students_mod.generate_students(num_students=5, seed=101)
        assert a == b

    def test_birthdate_range(self):
        cohort = students_mod.generate_students(num_students=50, seed=1)
        for s in cohort:
            assert 2000 <= s["birthdate"].year <= 2006

    def test_grades_range(self):
        cohort = students_mod.generate_students(num_students=20, seed=2)
        for s in cohort:
            assert len(s["grades"]) == 3
            assert all(0.0 <= g <= 20.0 for g in s["grades"])


class TestEnrichAndStats:
    def test_enrich_adds_age_and_average(self):
        cohort = students_mod.generate_students(num_students=4, seed=42)
        enriched = analysis_mod.enrich_student_data(cohort, reference_year=2026)
        for s in enriched:
            assert s["age"] == 2026 - s["birthdate"].year
            assert abs(s["average"] - round(sum(s["grades"]) / 3, 2)) < 1e-9

    def test_statistics_keys_and_values(self):
        cohort = analysis_mod.enrich_student_data(
            students_mod.generate_students(num_students=10, seed=101), reference_year=2026
        )
        stats = analysis_mod.compute_cohort_statistics(cohort)
        for key in ("mean", "median", "stdev", "min_average", "max_average", "mean_age"):
            assert key in stats
        assert stats["min_average"] <= stats["median"] <= stats["max_average"]
        assert stats["mean"] >= stats["min_average"]


# ---------------------------------------------------------------------------
# 04_One_Million_Record_Streaming
# ---------------------------------------------------------------------------
class TestGenerateLargeCsv:
    def test_generates_requested_rows(self, tmp_path):
        fp = tmp_path / "small.csv"
        gen_mod.generate_large_csv(str(fp), total_rows=25)
        text = fp.read_text()
        assert text.count("\n") == 26  # header + 25 rows
        assert text.splitlines()[0] == "PatientID,Age,BloodPressure"

    def test_deterministic_content(self, tmp_path):
        gen_mod.generate_large_csv(str(tmp_path / "a.csv"), total_rows=10)
        gen_mod.generate_large_csv(str(tmp_path / "b.csv"), total_rows=10)
        assert (tmp_path / "a.csv").read_text() == (tmp_path / "b.csv").read_text()

    def test_skips_existing_file(self, tmp_path, capsys):
        fp = tmp_path / "exists.csv"
        fp.write_text("already here\n")
        gen_mod.generate_large_csv(str(fp), total_rows=5)
        assert fp.read_text() == "already here\n"
        assert "already exists" in capsys.readouterr().out

    def test_row_formula(self, tmp_path):
        fp = tmp_path / "r.csv"
        gen_mod.generate_large_csv(str(fp), total_rows=3)
        rows = list(csv.reader(fp.read_text().splitlines()))
        assert rows[1] == ["P0000000", "20", "110"]
        assert rows[3] == ["P0000002", "22", "112"]


class TestStreaming:
    def _write(self, tmp_path):
        fp = tmp_path / "rows.csv"
        fp.write_text("PatientID,Age,BloodPressure\nP1,40,150\nP2,60,120\nP3,30,170\n")
        return fp

    def test_read_all_inefficient_returns_list_of_dicts(self, tmp_path):
        data = stream_mod.read_all_inefficient(str(self._write(tmp_path)))
        assert isinstance(data, list) and len(data) == 3
        assert data[0] == {"PatientID": "P1", "Age": "40", "BloodPressure": "150"}

    def test_stream_records_is_lazy_generator(self, tmp_path):
        gen = stream_mod.stream_records(str(self._write(tmp_path)))
        assert not isinstance(gen, list)
        rows = list(gen)
        assert len(rows) == 3

    def test_stream_counts_high_bp(self, tmp_path):
        count = sum(1 for r in stream_mod.stream_records(str(self._write(tmp_path)))
                    if int(r["BloodPressure"]) > 140)
        assert count == 2


# ---------------------------------------------------------------------------
# 07_Monthly_Sales_Forecasting
# ---------------------------------------------------------------------------
class TestGenerateRandomSales:
    def test_shape_and_bounds(self):
        out = utils07.generate_random_sales(10, 50, 100)
        assert out.shape == (100,)
        assert out.min() >= 10 and out.max() <= 50

    def test_dtype(self):
        assert utils07.generate_random_sales(0, 5, 10).dtype == np.dtype(int)

    def test_seeded_reproducibility(self):
        np.random.seed(123)
        a = utils07.generate_random_sales(5, 50, 12)
        np.random.seed(123)
        b = utils07.generate_random_sales(5, 50, 12)
        assert np.array_equal(a, b)
