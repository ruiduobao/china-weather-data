"""Tests for the --qa sidecar summary (Phase 5 optimization)."""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Load the module
HERE = Path(__file__).parent
_script_path = HERE.parent / "scripts" / "china-weather-data.py"
_spec = importlib.util.spec_from_file_location("china_weather_data", str(_script_path))
cwd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cwd)


class TestWriteQASummary(unittest.TestCase):
    def test_writes_json(self):
        with tempfile.TemporaryDirectory() as td:
            qa_path = os.path.join(td, "run.qa.json")
            args = cwd.argparse.Namespace(
                city="Beijing", station=None, lat=None, lon=None,
                start="2023-01-01", end="2023-01-31", type="temperature",
                output="out.csv", json=False, place=None, buffer_deg=0.6,
                province=None,
            )
            cwd.write_qa_summary(
                qa_path, skill="china-weather-data", command="download",
                args=args, payload={"n_records": 31},
            )
            self.assertTrue(os.path.exists(qa_path))
            data = json.loads(Path(qa_path).read_text(encoding="utf-8"))
            self.assertEqual(data["skill"], "china-weather-data")
            self.assertEqual(data["command"], "download")
            self.assertEqual(data["city"], "Beijing")
            self.assertEqual(data["start"], "2023-01-01")
            self.assertEqual(data["end"], "2023-01-31")
            self.assertEqual(data["type"], "temperature")
            self.assertEqual(data["n_records"], 31)
            self.assertIn("timestamp", data)
            self.assertIn("version", data)

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            qa_path = os.path.join(td, "nested", "subdir", "run.qa.json")
            args = cwd.argparse.Namespace()
            cwd.write_qa_summary(
                qa_path, skill="china-weather-data", command="download",
                args=args, payload={},
            )
            self.assertTrue(os.path.exists(qa_path))


class TestDownloadParser(unittest.TestCase):
    def test_download_accepts_qa(self):
        # We need a way to access the parser; refactor if not exposed.
        # Build a minimal parser like the script does.
        parser = cwd.argparse.ArgumentParser(prog="china-weather-data")
        sub = parser.add_subparsers(dest="command")
        p = sub.add_parser("download")
        p.add_argument("--city")
        p.add_argument("--lat", type=float)
        p.add_argument("--lon", type=float)
        p.add_argument("--start", required=True)
        p.add_argument("--end", required=True)
        p.add_argument("--type", default="temperature")
        p.add_argument("--output", required=True)
        p.add_argument("--qa", metavar="PATH", default=None)
        # Parse with all required + new flag
        ns = parser.parse_args([
            "download", "--city", "Beijing", "--start", "2023-01-01",
            "--end", "2023-01-31", "--output", "out.csv", "--qa", "out.qa.json",
        ])
        self.assertEqual(ns.qa, "out.qa.json")
        self.assertEqual(ns.output, "out.csv")


class TestCmdDownloadQA(unittest.TestCase):
    @patch("requests.get")
    def test_writes_sidecar_with_qa(self, mock_get):
        with tempfile.TemporaryDirectory() as td:
            qa_path = os.path.join(td, "out.qa.json")
            out_csv = os.path.join(td, "weather.csv")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "daily": {
                    "time": ["2023-01-01", "2023-01-02"],
                    "temperature_2m_mean": [1.0, 2.0],
                }
            }
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            args = cwd.argparse.Namespace(
                city="Beijing", station=None, lat=None, lon=None,
                start="2023-01-01", end="2023-01-02",
                type="temperature", output=out_csv, qa=qa_path,
            )
            rc = cwd.cmd_download(args)
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(os.path.exists(qa_path))
            data = json.loads(Path(qa_path).read_text(encoding="utf-8"))
            self.assertEqual(data["command"], "download")
            self.assertEqual(data["n_records"], 2)
            self.assertEqual(data["date_range"], ["2023-01-01", "2023-01-02"])
            self.assertIn("lat", data)
            self.assertIn("lon", data)
            self.assertTrue(data["output_path"].endswith("weather.csv"))

    @patch("requests.get")
    def test_no_sidecar_without_qa(self, mock_get):
        with tempfile.TemporaryDirectory() as td:
            out_csv = os.path.join(td, "weather.csv")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "daily": {
                    "time": ["2023-01-01"],
                    "temperature_2m_mean": [1.0],
                }
            }
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            args = cwd.argparse.Namespace(
                city="Beijing", station=None, lat=None, lon=None,
                start="2023-01-01", end="2023-01-01",
                type="temperature", output=out_csv, qa=None,
            )
            rc = cwd.cmd_download(args)
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(out_csv))
            # No sidecar should exist
            self.assertFalse(os.path.exists(os.path.join(td, "out.qa.json")))


if __name__ == "__main__":
    unittest.main()
