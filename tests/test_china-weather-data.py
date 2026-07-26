#!/usr/bin/env python3
"""Tests for china-weather-data CLI."""

import sys
import os
import json
import importlib.util
import unittest
from unittest.mock import patch, MagicMock

# Load the module
_script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "china-weather-data.py")
_spec = importlib.util.spec_from_file_location("china_weather_data", _script_path)
cwd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cwd)


class TestValidation(unittest.TestCase):
    def test_valid_date(self):
        self.assertTrue(cwd.validate_date("2020-01-01"))
        self.assertTrue(cwd.validate_date("2020-12-31"))

    def test_invalid_date(self):
        self.assertFalse(cwd.validate_date("2020-13-01"))
        self.assertFalse(cwd.validate_date("01-01-2020"))
        self.assertFalse(cwd.validate_date("not-a-date"))


class TestResolveCoordinates(unittest.TestCase):
    def test_city_lookup(self):
        result = cwd.resolve_coordinates("Beijing", None, None)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result[0], 39.9042, places=3)

    def test_direct_coords(self):
        result = cwd.resolve_coordinates(None, 40.0, 117.0)
        self.assertEqual(result, (40.0, 117.0))

    def test_unknown_city(self):
        # Patch Open-Meteo to return empty so the fallback does not rescue us
        from unittest.mock import patch
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"results": []}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp
            result = cwd.resolve_coordinates("Atlantis", None, None)
            self.assertIsNone(result)


class TestQueryOpenMeteo(unittest.TestCase):
    @patch("requests.get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "daily": {
                "time": ["2020-01-01", "2020-01-02"],
                "temperature_2m_mean": [5.0, 6.0],
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = cwd.query_open_meteo(39.9, 116.4, "2020-01-01", "2020-01-02")
        self.assertIsNotNone(result)
        self.assertIn("daily", result)

    @patch("requests.get")
    def test_timeout(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout()
        result = cwd.query_open_meteo(39.9, 116.4, "2020-01-01", "2020-01-02")
        self.assertIsNone(result)


class TestFormatResults(unittest.TestCase):
    def test_format_temperature(self):
        data = {
            "daily": {
                "time": ["2020-01-01", "2020-01-02"],
                "temperature_2m_mean": [5.0, 6.0],
                "temperature_2m_max": [10.0, 11.0],
            }
        }
        records = cwd.format_open_meteo_results(data, "temperature")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["date"], "2020-01-01")
        self.assertAlmostEqual(records[0]["temperature_2m_mean"], 5.0)


class TestCLI(unittest.TestCase):
    @patch("requests.get")
    def test_query_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "daily": {"time": ["2020-01-01"], "temperature_2m_mean": [5.0]}
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        args = cwd.argparse.Namespace(
            city="Beijing", station=None, lat=None, lon=None,
            start="2020-01-01", end="2020-01-31", type="temperature", json=False,
        )
        rc = cwd.cmd_query(args)
        self.assertEqual(rc, 0)

    def test_query_invalid_date(self):
        args = cwd.argparse.Namespace(
            city="Beijing", station=None, lat=None, lon=None,
            start="invalid", end="2020-01-31", type="temperature", json=False,
        )
        rc = cwd.cmd_query(args)
        self.assertEqual(rc, 1)

    def test_configure(self):
        args = cwd.argparse.Namespace(key="test_key_123")
        with patch("os.makedirs"):
            with patch("builtins.open", MagicMock()):
                rc = cwd.cmd_configure(args)
                self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
