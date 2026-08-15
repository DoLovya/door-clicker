import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module
import auth
from config_manager import ConfigManager


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")

        ConfigManager._instance = None
        self.config_mgr = ConfigManager()
        self.config_mgr._config_path = self.config_path
        self.config_mgr.load_config()

        self.mock_mqtt = MagicMock()
        self.mock_mqtt.connect.return_value = {
            "success": True, "message": "Connected successfully"
        }
        self.mock_mqtt.reload_config.return_value = {
            "success": True, "message": "Config reloaded (not connected)"
        }
        self.mock_mqtt.is_connected.return_value = False
        self.mock_mqtt.publish_open_door.return_value = {
            "success": True, "message": "Door open command sent"
        }
        self.mock_mqtt.test_connection.return_value = {
            "success": True, "message": "Connection successful"
        }
        self.mock_mqtt.get_subscribed_topics.return_value = []
        self.mock_mqtt.subscribe_topic.return_value = {
            "success": True, "message": "Subscribed to topic/test"
        }
        self.mock_mqtt.unsubscribe_topic.return_value = {
            "success": True, "message": "Unsubscribed from topic/test"
        }

        self._saved_config = app_module.config_manager
        self._saved_mqtt = app_module.mqtt_client_manager
        app_module.config_manager = self.config_mgr
        app_module.mqtt_client_manager = self.mock_mqtt

        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        self._hash_patcher = patch('auth._get_stored_hash',
            return_value=hashlib.sha256(b"admin").hexdigest())
        self._hash_patcher.start()

        self.client.post('/api/auth/login',
            json={"username": "admin", "password": "admin"})

    def tearDown(self):
        self._hash_patcher.stop()
        app_module.config_manager = self._saved_config
        app_module.mqtt_client_manager = self._saved_mqtt
        ConfigManager._instance = None
        self.temp_dir.cleanup()

    def test_health(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"status": "ok"})

    def test_get_config(self):
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["mqttServer"], "127.0.0.1")
        self.assertEqual(data["mqttPort"], 1883)
        self.assertEqual(data["mqttUsername"], "")
        self.assertEqual(data["mqttPassword"], "")
        self.assertEqual(data["topics"], [])

    def test_save_and_read_config(self):
        self.config_mgr.update_config({
            "mqttServer": "192.168.1.1",
            "mqttPort": 8883,
        })

        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["mqttServer"], "192.168.1.1")
        self.assertEqual(data["mqttPort"], 8883)
        self.assertEqual(data["mqttUsername"], "")
        self.assertEqual(data["mqttPassword"], "")

    def test_hot_reload(self):
        self.config_mgr.update_config({
            "mqttServer": "10.0.0.1",
            "mqttPort": 4444,
        })

        response = self.client.put('/api/config', json={
            "mqttServer": "10.0.0.2",
            "mqttPort": 5555,
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("reload", data)
        self.assertTrue(data["reload"]["success"])
        self.mock_mqtt.reload_config.assert_called_once()

    def test_full_flow(self):
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["mqttServer"], "127.0.0.1")
        self.assertEqual(data["mqttPort"], 1883)

        response = self.client.put('/api/config', json={
            "mqttServer": "10.0.0.1",
            "mqttPort": 8883,
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("config", data)
        self.assertIn("reload", data)
        self.assertEqual(data["config"]["mqttServer"], "10.0.0.1")
        self.assertEqual(data["config"]["mqttPort"], 8883)
        self.assertTrue(data["reload"]["success"])

        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["mqttServer"], "10.0.0.1")
        self.assertEqual(data["mqttPort"], 8883)

        response = self.client.get('/api/mqtt/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("connected", data)
        self.assertFalse(data["connected"])

    def test_config_persistence(self):
        self.config_mgr.update_config({
            "mqttServer": "persistent.local",
            "mqttPort": 9999,
            "mqttUsername": "testuser",
            "mqttPassword": "testpass",
        })

        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["mqttServer"], "persistent.local")
        self.assertEqual(data["mqttPort"], 9999)

        ConfigManager._instance = None
        new_mgr = ConfigManager()
        new_mgr._config_path = self.config_path
        new_mgr.load_config()

        cfg = new_mgr.get_config()
        self.assertEqual(cfg["mqttServer"], "persistent.local")
        self.assertEqual(cfg["mqttPort"], 9999)
        self.assertEqual(cfg["mqttUsername"], "testuser")
        self.assertEqual(cfg["mqttPassword"], "testpass")
        self.assertEqual(cfg["topics"], [])


if __name__ == '__main__':
    unittest.main()