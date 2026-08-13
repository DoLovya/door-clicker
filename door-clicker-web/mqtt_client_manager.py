import json
import threading

import paho.mqtt.client as mqtt

from config_manager import ConfigManager

try:
    _CALLBACK_API_VERSION = mqtt.CallbackAPIVersion.VERSION2
except AttributeError:
    _CALLBACK_API_VERSION = 1


class MqttClientManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._client = None
        self._connected = False
        self._subscribed_topics = set()
        self._config_manager = ConfigManager()
        self._on_message_callback = None
        self._client_id = f"door_clicker_{threading.get_ident()}"

    @property
    def on_message_callback(self):
        return self._on_message_callback

    @on_message_callback.setter
    def on_message_callback(self, callback):
        self._on_message_callback = callback

    def _on_connect(self, client, userdata, *args):
        if _CALLBACK_API_VERSION == 2:
            reason_code = args[1]
        else:
            reason_code = args[1] if len(args) > 1 else -1

        if reason_code == 0:
            self._connected = True
            for topic in self._subscribed_topics:
                client.subscribe(topic)
        else:
            self._connected = False

    def _on_disconnect(self, client, userdata, *args):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        if self._on_message_callback:
            try:
                self._on_message_callback(client, userdata, msg)
            except Exception:
                pass

    def connect(self):
        try:
            config = self._config_manager.get_config()
            self._client = mqtt.Client(
                callback_api_version=_CALLBACK_API_VERSION,
                client_id=self._client_id,
            )
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message

            username = config.get("mqttUsername", "")
            password = config.get("mqttPassword", "")
            if username:
                self._client.username_pw_set(username, password)

            self._client.connect(
                config["mqttServer"],
                config["mqttPort"],
                keepalive=60,
            )
            self._client.loop_start()
            self._connected = True
            return {"success": True, "message": "Connected successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def disconnect(self):
        try:
            if self._client:
                self._client.loop_stop()
                self._client.disconnect()
            self._connected = False
            return {"success": True, "message": "Disconnected successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def is_connected(self):
        return self._connected

    def test_connection(self, timeout=5):
        try:
            config = self._config_manager.get_config()
            test_client = mqtt.Client(
                callback_api_version=_CALLBACK_API_VERSION,
                client_id=f"test_{threading.get_ident()}",
            )

            connected_event = threading.Event()
            result = {"success": False, "message": ""}

            def _on_connect(client, userdata, *args):
                if _CALLBACK_API_VERSION == 2:
                    reason_code = args[1]
                else:
                    reason_code = args[1] if len(args) > 1 else -1

                if reason_code == 0:
                    result["success"] = True
                    result["message"] = "Connection successful"
                else:
                    result["success"] = False
                    result["message"] = f"Connection failed with code: {reason_code}"
                connected_event.set()

            def _on_disconnect(client, userdata, *args):
                pass

            test_client.on_connect = _on_connect
            test_client.on_disconnect = _on_disconnect

            username = config.get("mqttUsername", "")
            password = config.get("mqttPassword", "")
            if username:
                test_client.username_pw_set(username, password)

            test_client.connect(
                config["mqttServer"],
                config["mqttPort"],
                keepalive=timeout,
            )
            test_client.loop_start()

            if connected_event.wait(timeout=timeout):
                test_client.loop_stop()
                test_client.disconnect()
                return result
            else:
                test_client.loop_stop()
                test_client.disconnect()
                return {"success": False, "message": f"Connection timeout after {timeout}s"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def subscribe_topic(self, topic):
        try:
            if not self._client or not self._connected:
                return {"success": False, "message": "Not connected to MQTT broker"}
            result = self._client.subscribe(topic)
            if result[0] == 0:
                self._subscribed_topics.add(topic)
                return {"success": True, "message": f"Subscribed to {topic}"}
            else:
                return {"success": False, "message": f"Subscribe failed with code: {result[0]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def unsubscribe_topic(self, topic):
        try:
            if not self._client or not self._connected:
                return {"success": False, "message": "Not connected to MQTT broker"}
            result = self._client.unsubscribe(topic)
            if result[0] == 0:
                self._subscribed_topics.discard(topic)
                return {"success": True, "message": f"Unsubscribed from {topic}"}
            else:
                return {"success": False, "message": f"Unsubscribe failed with code: {result[0]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_subscribed_topics(self):
        return list(self._subscribed_topics)

    def publish_open_door(self):
        try:
            if not self._client or not self._connected:
                return {"success": False, "message": "Not connected to MQTT broker"}
            command_payload = json.dumps([
                {"angle": 90, "duration": 200},
                {"angle": 0, "duration": 200},
            ])
            result = self._client.publish("data", command_payload)
            result.wait_for_publish()
            if result.is_published():
                return {"success": True, "message": "Door open command sent"}
            else:
                return {"success": False, "message": "Failed to publish door open command"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def reload_config(self):
        try:
            was_connected = self._connected
            if was_connected:
                self.disconnect()
            self._config_manager.load_config()
            if was_connected:
                result = self.connect()
                if result["success"]:
                    return {"success": True, "message": "Config reloaded and reconnected"}
                else:
                    return {
                        "success": False,
                        "message": f"Config reloaded but reconnection failed: {result['message']}",
                    }
            return {"success": True, "message": "Config reloaded (not connected)"}
        except Exception as e:
            return {"success": False, "message": str(e)}