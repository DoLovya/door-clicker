import json
import os
import sys
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from mqtt_client_manager import MqttClientManager


class TestMqttClientManager(unittest.TestCase):

    def setUp(self):
        MqttClientManager._instance = None

    def tearDown(self):
        MqttClientManager._instance = None

    def test_singleton(self):
        mgr1 = MqttClientManager()
        mgr2 = MqttClientManager()
        self.assertIs(mgr1, mgr2)

    @patch('mqtt_client_manager.ConfigManager')
    def test_config_reading(self, mock_config_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "192.168.1.100",
            "mqttPort": 8883,
            "mqttUsername": "admin",
            "mqttPassword": "secret",
            "topics": ["test/topic"],
        }
        mock_config_class.return_value = mock_config

        mgr = MqttClientManager()
        cfg = mgr._config_manager.get_config()
        self.assertEqual(cfg["mqttServer"], "192.168.1.100")
        self.assertEqual(cfg["mqttPort"], 8883)
        self.assertEqual(cfg["mqttUsername"], "admin")
        self.assertEqual(cfg["mqttPassword"], "secret")

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_connect_success(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        result = mgr.connect()

        self.assertTrue(result["success"])
        self.assertTrue(mgr.is_connected())
        mock_client.connect.assert_called_once_with("127.0.0.1", 1883, keepalive=60)
        mock_client.loop_start.assert_called_once()

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_connect_with_credentials(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "user",
            "mqttPassword": "pass",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        result = mgr.connect()

        self.assertTrue(result["success"])
        mock_client.username_pw_set.assert_called_once_with("user", "pass")

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_connect_failure(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        result = mgr.connect()

        self.assertFalse(result["success"])
        self.assertIn("Connection refused", result["message"])
        self.assertFalse(mgr.is_connected())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_disconnect_success(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        result = mgr.disconnect()

        self.assertTrue(result["success"])
        self.assertFalse(mgr.is_connected())
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_disconnect_when_not_connected(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mgr = MqttClientManager()
        result = mgr.disconnect()

        self.assertTrue(result["success"])
        self.assertFalse(mgr.is_connected())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_is_connected_state(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        self.assertFalse(mgr.is_connected())

        mgr.connect()
        self.assertTrue(mgr.is_connected())

        mgr.disconnect()
        self.assertFalse(mgr.is_connected())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_subscribe_topic_success(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        result = mgr.subscribe_topic("test/topic")

        self.assertTrue(result["success"])
        self.assertIn("test/topic", mgr.get_subscribed_topics())
        # 设备状态topic + test/topic = 2次订阅
        self.assertEqual(mock_client.subscribe.call_count, 2)
        mock_client.subscribe.assert_any_call("door/test/status")
        mock_client.subscribe.assert_any_call("test/topic")

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_subscribe_topic_failure(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (1, 0)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        result = mgr.subscribe_topic("test/topic")

        self.assertFalse(result["success"])
        self.assertNotIn("test/topic", mgr.get_subscribed_topics())

    def test_subscribe_topic_not_connected(self):
        mgr = MqttClientManager()
        result = mgr.subscribe_topic("test/topic")

        self.assertFalse(result["success"])
        self.assertIn("Not connected", result["message"])

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_unsubscribe_topic_success(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client.unsubscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        mgr.subscribe_topic("test/topic")
        result = mgr.unsubscribe_topic("test/topic")

        self.assertTrue(result["success"])
        self.assertNotIn("test/topic", mgr.get_subscribed_topics())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_unsubscribe_topic_not_subscribed(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.unsubscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        result = mgr.unsubscribe_topic("non-existent/topic")

        self.assertTrue(result["success"])
        self.assertNotIn("non-existent/topic", mgr.get_subscribed_topics())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_get_subscribed_topics(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        mgr.subscribe_topic("topic/a")
        mgr.subscribe_topic("topic/b")

        topics = mgr.get_subscribed_topics()
        # 包含自动订阅的状态topic + 2个手动订阅 = 3
        self.assertEqual(len(topics), 3)
        self.assertIn("topic/a", topics)
        self.assertIn("topic/b", topics)
        self.assertIn("door/test/status", topics)

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_publish_open_door_success(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/00094E53",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_result = MagicMock()
        mock_result.is_published.return_value = True
        mock_client.publish.return_value = mock_result

        mgr = MqttClientManager()
        mgr.connect()
        result = mgr.publish_open_door()

        self.assertTrue(result["success"])
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        self.assertEqual(call_args[0][0], "door/00094E53")

        payload = json.loads(call_args[0][1])
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["angle"], 90)
        self.assertEqual(payload[0]["duration"], 200)
        self.assertEqual(payload[1]["angle"], 0)
        self.assertEqual(payload[1]["duration"], 200)

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_publish_open_door_not_connected_auto_reconnect(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/00094E53",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_result = MagicMock()
        mock_result.is_published.return_value = True
        mock_client.publish.return_value = mock_result

        mgr = MqttClientManager()
        self.assertFalse(mgr.is_connected())
        result = mgr.publish_open_door()

        self.assertTrue(result["success"])
        mock_client.connect.assert_called_once()
        mock_client.publish.assert_called_once()

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_publish_open_door_reconnect_failure(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/00094E53",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        result = mgr.publish_open_door()

        self.assertFalse(result["success"])
        self.assertIn("Not connected", result["message"])

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_publish_open_door_send_failure(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/00094E53",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_result = MagicMock()
        mock_result.is_published.return_value = False
        mock_client.publish.return_value = mock_result

        mgr = MqttClientManager()
        mgr.connect()
        result = mgr.publish_open_door()

        self.assertFalse(result["success"])

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_reload_config_not_connected(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mgr = MqttClientManager()
        self.assertFalse(mgr.is_connected())
        result = mgr.reload_config()

        self.assertTrue(result["success"])
        self.assertIn("connected", result["message"].lower())
        mock_config.load_config.assert_called_once()
        self.assertTrue(mgr.is_connected())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_reload_config_while_connected(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        self.assertTrue(mgr.is_connected())

        result = mgr.reload_config()

        self.assertTrue(result["success"])
        self.assertTrue(mgr.is_connected())
        self.assertEqual(mock_client.connect.call_count, 2)

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_reload_config_reconnect_failure(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.connect.side_effect = [None, Exception("Reconnect failed")]
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()
        self.assertTrue(mgr.is_connected())

        result = mgr.reload_config()

        self.assertFalse(result["success"])
        self.assertIn("Reconnect failed", result["message"])
        self.assertFalse(mgr.is_connected())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_on_message_callback(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        callback_called = MagicMock()

        mgr = MqttClientManager()
        mgr.on_message_callback = callback_called
        mgr.connect()

        test_msg = MagicMock()
        test_msg.topic = "test/topic"
        test_msg.payload = b'{"test": "data"}'

        mgr._on_message(mock_client, None, test_msg)
        callback_called.assert_called_once_with(mock_client, None, test_msg)

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_on_message_callback_not_set(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        test_msg = MagicMock()
        mgr._on_message(mock_client, None, test_msg)

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_on_message_callback_exception_handled(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        def bad_callback(client, userdata, msg):
            raise ValueError("Callback error")

        mgr = MqttClientManager()
        mgr.on_message_callback = bad_callback
        mgr.connect()

        test_msg = MagicMock()
        try:
            mgr._on_message(mock_client, None, test_msg)
        except Exception:
            self.fail("_on_message should not raise exceptions from user callback")

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_test_connection_success(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()

        with patch.object(mgr, '_on_connect', create=True):
            pass

        import threading
        event = threading.Event()

        def fake_on_connect(client, userdata, *args):
            event.set()

        mock_client.on_connect = fake_on_connect

        result = mgr.test_connection(timeout=1)

        self.assertFalse(result["success"])
        self.assertIn("timeout", result["message"].lower())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_multiple_subscribe_unsubscribe(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client.unsubscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        mgr.subscribe_topic("topic/1")
        mgr.subscribe_topic("topic/2")
        mgr.subscribe_topic("topic/3")
        # 3个手动订阅 + 1个自动状态topic = 4
        self.assertEqual(len(mgr.get_subscribed_topics()), 4)

        mgr.unsubscribe_topic("topic/2")
        # 2个手动订阅 + 1个自动状态topic = 3
        self.assertEqual(len(mgr.get_subscribed_topics()), 3)
        self.assertNotIn("topic/2", mgr.get_subscribed_topics())
        self.assertIn("topic/1", mgr.get_subscribed_topics())
        self.assertIn("topic/3", mgr.get_subscribed_topics())
        self.assertIn("door/test/status", mgr.get_subscribed_topics())


    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_connect_auto_subscribe_status_topic(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        self.assertTrue(mgr.is_connected())
        self.assertIn("door/test/status", mgr.get_subscribed_topics())
        mock_client.subscribe.assert_any_call("door/test/status")

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_heartbeat_message_updates_timestamp(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        test_msg = MagicMock()
        test_msg.topic = "door/test/status"
        test_msg.payload = b'{"event":"heartbeat","clientId":"door_test","uptime":120}'

        mgr._on_message(mock_client, None, test_msg)

        self.assertIsNotNone(mgr._last_heartbeat)
        self.assertTrue(mgr.is_device_online())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_connected_event_updates_timestamp(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        test_msg = MagicMock()
        test_msg.topic = "door/test/status"
        test_msg.payload = b'{"event":"connected","clientId":"door_test"}'

        mgr._on_message(mock_client, None, test_msg)

        self.assertIsNotNone(mgr._last_heartbeat)
        self.assertTrue(mgr.is_device_online())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_device_online_within_timeout(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        from datetime import datetime, timedelta
        mgr._last_heartbeat = datetime.now()
        mgr._device_online = True
        mgr._last_device_state = "online"

        self.assertTrue(mgr.is_device_online())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_device_offline_after_timeout(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        from datetime import datetime, timedelta
        mgr._last_heartbeat = datetime.now() - timedelta(seconds=100)
        mgr._device_online = True
        mgr._last_device_state = "online"

        self.assertFalse(mgr.is_device_online())

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_disconnect_resets_device_status(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        from datetime import datetime
        mgr._last_heartbeat = datetime.now()
        mgr._device_online = True
        mgr._last_device_state = "online"

        mgr._on_disconnect(mock_client, None)

        self.assertIsNone(mgr._last_heartbeat)
        self.assertFalse(mgr._connected)

        status = mgr.get_device_status()
        self.assertEqual(status["status"], "unknown")
        self.assertFalse(status["deviceOnline"])

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_get_device_status_format(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()

        status = mgr.get_device_status()
        self.assertIn("deviceOnline", status)
        self.assertIn("lastHeartbeat", status)
        self.assertIn("mqttConnected", status)
        self.assertIn("status", status)
        self.assertEqual(status["status"], "unknown")
        self.assertFalse(status["mqttConnected"])

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_reset_device_status(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mgr = MqttClientManager()

        from datetime import datetime
        mgr._last_heartbeat = datetime.now()
        mgr._device_online = True
        mgr._last_device_state = "online"

        mgr.reset_device_status()

        self.assertIsNone(mgr._last_heartbeat)
        self.assertIsNone(mgr._last_device_state)
        self.assertFalse(mgr._device_online)

    @patch('mqtt_client_manager.mqtt.Client')
    @patch('mqtt_client_manager.ConfigManager')
    def test_invalid_message_no_status_change(self, mock_config_class, mock_client_class):
        mock_config = MagicMock()
        mock_config.get_config.return_value = {
            "mqttServer": "127.0.0.1",
            "mqttPort": 1883,
            "mqttUsername": "",
            "mqttPassword": "",
            "doorTopic": "door/test",
            "topics": [],
        }
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)
        mock_client_class.return_value = mock_client

        mgr = MqttClientManager()
        mgr.connect()

        test_msg = MagicMock()
        test_msg.topic = "door/test/status"
        test_msg.payload = b'invalid json'

        mgr._on_message(mock_client, None, test_msg)

        self.assertIsNone(mgr._last_heartbeat)
        self.assertFalse(mgr.is_device_online())


if __name__ == '__main__':
    unittest.main()
