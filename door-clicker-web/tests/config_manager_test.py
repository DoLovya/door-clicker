import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        ConfigManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")

    def tearDown(self):
        ConfigManager._instance = None
        self.temp_dir.cleanup()

    def _make_manager(self):
        mgr = ConfigManager()
        mgr._config_path = self.config_path
        mgr.load_config()
        return mgr

    def test_default_values(self):
        mgr = self._make_manager()
        cfg = mgr.get_config()
        self.assertEqual(cfg["mqttServer"], "127.0.0.1")
        self.assertEqual(cfg["mqttPort"], 1883)
        self.assertEqual(cfg["mqttUsername"], "")
        self.assertEqual(cfg["mqttPassword"], "")
        self.assertEqual(cfg["topics"], [])

    def test_get_default_config_static(self):
        default = ConfigManager.get_default_config()
        self.assertEqual(default["mqttServer"], "127.0.0.1")
        default["mqttServer"] = "changed"
        self.assertEqual(ConfigManager.get_default_config()["mqttServer"], "127.0.0.1")

    def test_save_and_load(self):
        mgr = self._make_manager()
        new_cfg = {
            "mqttServer": "192.168.1.100",
            "mqttPort": 8883,
            "mqttUsername": "admin",
            "mqttPassword": "secret",
            "topics": ["topic/a", "topic/b"],
        }
        result = mgr.save_config(new_cfg)
        self.assertTrue(result)

        ConfigManager._instance = None
        mgr2 = self._make_manager()
        loaded = mgr2.get_config()
        self.assertEqual(loaded["mqttServer"], "192.168.1.100")
        self.assertEqual(loaded["mqttPort"], 8883)
        self.assertEqual(loaded["mqttUsername"], "admin")
        self.assertEqual(loaded["mqttPassword"], "secret")
        self.assertEqual(loaded["topics"], ["topic/a", "topic/b"])

    def test_corrupted_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{ this is not valid json !!! }")

        mgr = self._make_manager()
        cfg = mgr.get_config()
        self.assertEqual(cfg["mqttServer"], "127.0.0.1")
        self.assertEqual(cfg["mqttPort"], 1883)

    def test_missing_file_uses_defaults(self):
        mgr = self._make_manager()
        cfg = mgr.get_config()
        self.assertEqual(cfg["mqttServer"], "127.0.0.1")

    def test_partial_update(self):
        mgr = self._make_manager()
        result = mgr.update_config({"mqttServer": "10.0.0.1", "mqttPort": 9999})
        self.assertEqual(result["mqttServer"], "10.0.0.1")
        self.assertEqual(result["mqttPort"], 9999)
        self.assertEqual(result["mqttUsername"], "")
        self.assertEqual(result["topics"], [])

        with open(self.config_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["mqttServer"], "10.0.0.1")
        self.assertEqual(saved["mqttPort"], 9999)

    def test_update_ignores_unknown_keys(self):
        mgr = self._make_manager()
        result = mgr.update_config({"unknownKey": "value", "mqttServer": "10.0.0.2"})
        self.assertNotIn("unknownKey", result)
        self.assertEqual(result["mqttServer"], "10.0.0.2")

    def test_get_config_returns_copy(self):
        mgr = self._make_manager()
        cfg1 = mgr.get_config()
        cfg1["mqttServer"] = "mutated"
        cfg2 = mgr.get_config()
        self.assertEqual(cfg2["mqttServer"], "127.0.0.1")

    def test_singleton(self):
        mgr1 = self._make_manager()
        mgr2 = self._make_manager()
        self.assertIs(mgr1, mgr2)

    def test_save_config_invalid_data(self):
        mgr = self._make_manager()
        result = mgr.save_config(None)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
