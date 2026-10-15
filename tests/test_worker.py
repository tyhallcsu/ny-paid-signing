"""Offline worker regressions: no dotenv, network, or production database access."""
import ast
import contextlib
import importlib.util
import io
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        dotenv = types.ModuleType('dotenv')
        dotenv.load_dotenv = Mock()  # Never read the user's .env.
        spec = importlib.util.spec_from_file_location('worker_under_test', ROOT/'worker/worker.py')
        self.worker = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'dotenv': dotenv}), patch.dict('os.environ', {}, clear=True):
            spec.loader.exec_module(self.worker)
        self.worker.DB_PATH = str(Path(self.temp.name)/'test.db')
        with sqlite3.connect(self.worker.DB_PATH) as conn:
            conn.execute('CREATE TABLE devices (udid TEXT, device_name TEXT, apple_registered INTEGER)')
            conn.execute("INSERT INTO devices VALUES ('synthetic-id','Test device',0)")

    def tearDown(self):
        self.temp.cleanup()

    def run_real(self, team):
        api = types.ModuleType('PyDunk')
        api.Anisette = Mock()
        api.GSUserAuth = Mock()
        api.GSAuthSync = Mock()
        api.XcodeAPI = Mock()
        api.XcodeAPI.from_gsauth.return_value.teams = [team]
        with patch.dict(sys.modules, {'PyDunk': api}), contextlib.redirect_stdout(io.StringIO()):
            self.worker.run_real()

    def test_all_python_sources_parse(self):
        for path in ROOT.rglob('*.py'):
            if '.venv' not in path.parts:
                ast.parse(path.read_text(), filename=str(path))

    def test_new_device_registered_only_after_success(self):
        team = types.SimpleNamespace(devices=[],team_id='synthetic-team',_x=Mock())
        team._x._pr.return_value = {'resultCode':0}
        self.run_real(team)
        team._x._pr.assert_called_once()
        self.assertEqual(self.worker.get_pending(), [])

    def test_failed_registration_stays_pending(self):
        team = types.SimpleNamespace(devices=[],team_id='synthetic-team',_x=Mock())
        team._x._pr.return_value = {'resultCode':1,'userString':'synthetic rejection'}
        self.run_real(team)
        self.assertEqual(len(self.worker.get_pending()), 1)

    def test_existing_device_does_not_register_again(self):
        team = types.SimpleNamespace(devices=[types.SimpleNamespace(device_number='synthetic-id')],_x=Mock())
        self.run_real(team)
        team._x._pr.assert_not_called()
        self.assertEqual(self.worker.get_pending(), [])

    def test_malformed_response_stays_pending(self):
        team = types.SimpleNamespace(devices=[],team_id='synthetic-team',_x=Mock())
        team._x._pr.return_value = None
        self.run_real(team)
        self.assertEqual(len(self.worker.get_pending()), 1)

if __name__ == '__main__':
    unittest.main()
