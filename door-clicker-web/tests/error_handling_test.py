import hashlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import app as app_module
import auth


class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_mqtt = MagicMock()

        default_cfg = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "adminUser": "admin",
            "topics": [],
        }
        self.mock_config.get_config.return_value = default_cfg
        self.mock_config.update_config.return_value = default_cfg

        self.mock_mqtt.publish_open_door.return_value = {
            "success": True, "message": "Door open command sent"
        }
        self.mock_mqtt.test_connection.return_value = {
            "success": True, "message": "Connection successful"
        }
        self.mock_mqtt.is_connected.return_value = True
        self.mock_mqtt.get_subscribed_topics.return_value = ["topic1", "topic2"]
        self.mock_mqtt.subscribe_topic.return_value = {
            "success": True, "message": "Subscribed to topic/test"
        }
        self.mock_mqtt.unsubscribe_topic.return_value = {
            "success": True, "message": "Unsubscribed from topic/test"
        }
        self.mock_mqtt.reload_config.return_value = {
            "success": True, "message": "Config reloaded and reconnected"
        }

        self._saved_config = app_module.config_manager
        self._saved_mqtt = app_module.mqtt_client_manager
        app_module.config_manager = self.mock_config
        app_module.mqtt_client_manager = self.mock_mqtt

        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.app.config['PROPAGATE_EXCEPTIONS'] = False
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

    def test_404_error_handler(self):
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data, {"error": "Not Found"})

    def test_404_error_handler_post(self):
        response = self.client.post('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data, {"error": "Not Found"})

    def test_500_error_handler(self):
        self.mock_mqtt.publish_open_door.side_effect = Exception("Unexpected error")
        response = self.client.post('/api/open/door')
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data, {"error": "Internal Server Error"})

    def test_update_config_invalid_port_not_integer(self):
        response = self.client.put('/api/config',
            json={"mqttPort": "1883"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttPort must be an integer")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_port_boolean(self):
        response = self.client.put('/api/config',
            json={"mqttPort": True})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttPort must be an integer")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_port_too_low(self):
        response = self.client.put('/api/config',
            json={"mqttPort": 0})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttPort must be between 1 and 65535")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_port_too_high(self):
        response = self.client.put('/api/config',
            json={"mqttPort": 65536})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttPort must be between 1 and 65535")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_server_not_string(self):
        response = self.client.put('/api/config',
            json={"mqttServer": 123})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttServer must be a string")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_server_empty(self):
        response = self.client.put('/api/config',
            json={"mqttServer": ""})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttServer must be a non-empty string")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_server_whitespace(self):
        response = self.client.put('/api/config',
            json={"mqttServer": "   "})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "mqttServer must be a non-empty string")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_topics_not_array(self):
        response = self.client.put('/api/config',
            json={"topics": "not_an_array"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Topics must be an array")
        self.mock_config.update_config.assert_not_called()

    def test_update_config_invalid_json(self):
        response = self.client.put('/api/config',
            content_type='application/json',
            data='not valid json')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Request body must be valid JSON")

    def test_update_config_valid(self):
        response = self.client.put('/api/config',
            json={"mqttServer": "192.168.1.1", "mqttPort": 1884})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("config", data)
        self.assertIn("reload", data)
        self.assertTrue(data["reload"]["success"])
        self.mock_config.update_config.assert_called_once()
        self.mock_mqtt.reload_config.assert_called_once()

    def test_add_topic_not_string(self):
        response = self.client.post('/api/topics',
            json={"topic": 123})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Topic must be a string")
        self.mock_mqtt.subscribe_topic.assert_not_called()

    def test_add_topic_empty(self):
        response = self.client.post('/api/topics',
            json={"topic": ""})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Topic must be a non-empty string")
        self.mock_mqtt.subscribe_topic.assert_not_called()

    def test_add_topic_whitespace(self):
        response = self.client.post('/api/topics',
            json={"topic": "   "})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Topic must be a non-empty string")
        self.mock_mqtt.subscribe_topic.assert_not_called()

    def test_add_topic_missing_field(self):
        response = self.client.post('/api/topics', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Request body must contain 'topic' field")
        self.mock_mqtt.subscribe_topic.assert_not_called()

    def test_add_topic_invalid_json(self):
        response = self.client.post('/api/topics',
            content_type='application/json',
            data='not json')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Request body must contain 'topic' field")

    def test_add_topic_valid(self):
        response = self.client.post('/api/topics',
            json={"topic": "sensor/data"})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.mock_mqtt.subscribe_topic.assert_called_with("sensor/data")


if __name__ == '__main__':
    unittest.main()
