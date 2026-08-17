import json
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from config_manager import ConfigManager
from log_manager import LogManager

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
        self._log_manager = LogManager()
        self._on_message_callback = None
        self._client_id = f"door_clicker_{threading.get_ident()}"
        self._device_online = False
        self._last_heartbeat = None
        self._device_status_topic = None
        self._last_device_state = None
        self._DEVICE_OFFLINE_TIMEOUT = 90

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
            self._log_manager.log_info("MQTT 连接成功")
            self._subscribe_device_status_topic()
            for topic in self._subscribed_topics:
                client.subscribe(topic)
        else:
            self._connected = False
            self._log_manager.log_error(f"MQTT 连接失败 (code: {reason_code})")

    def _subscribe_device_status_topic(self):
        config = self._config_manager.get_config()
        door_topic = config.get("doorTopic", "door/00094E53")
        self._device_status_topic = f"{door_topic}/status"

        if self._client and self._connected:
            result = self._client.subscribe(self._device_status_topic)
            if result[0] == 0:
                self._subscribed_topics.add(self._device_status_topic)
                self._log_manager.log_info(f"已订阅设备状态主题: {self._device_status_topic}")
            else:
                self._log_manager.log_error(f"订阅设备状态主题失败: {result[0]}")

    def _on_disconnect(self, client, userdata, *args):
        self._connected = False
        if self._last_device_state is not None:
            self._check_device_state_change(None)
        self._last_heartbeat = None
        self._log_manager.log_info("MQTT 连接已断开")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        self._log_manager.log_receive(msg.topic, payload)

        if self._device_status_topic and msg.topic == self._device_status_topic:
            self._handle_device_status_message(payload)

        if self._on_message_callback:
            try:
                self._on_message_callback(client, userdata, msg)
            except Exception:
                pass

    def _handle_device_status_message(self, payload):
        try:
            data = json.loads(payload)
            event = data.get("event", "")

            if event in ("heartbeat", "connected"):
                now = datetime.now()
                self._last_heartbeat = now
                self._check_device_state_change("online")

        except json.JSONDecodeError:
            self._log_manager.log_error(f"设备状态消息解析失败: {payload}")

    def _check_device_state_change(self, new_state):
        if self._last_device_state != new_state:
            self._last_device_state = new_state
            if new_state == "online":
                self._device_online = True
                self._log_manager.log_info("设备已上线")
            else:
                self._device_online = False
                self._log_manager.log_info("设备已离线")

    def connect(self):
        try:
            config = self._config_manager.get_config()
            self._log_manager.log_info(f"正在连接 MQTT {config['mqttServer']}:{config['mqttPort']}")
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
            self._subscribe_device_status_topic()
            return {"success": True, "message": "Connected successfully"}
        except Exception as e:
            self._log_manager.log_error(f"MQTT 连接异常: {str(e)}")
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

    def is_device_online(self):
        if self._last_heartbeat is None:
            return False

        elapsed = (datetime.now() - self._last_heartbeat).total_seconds()
        if elapsed <= self._DEVICE_OFFLINE_TIMEOUT:
            return True
        else:
            if self._device_online:
                self._check_device_state_change("offline")
            return False

    def get_device_status(self):
        self._device_online = self.is_device_online()

        last_heartbeat_str = None
        if self._last_heartbeat:
            last_heartbeat_str = self._last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")

        if not self._connected:
            status = "unknown"
        elif self._device_online:
            status = "online"
        elif self._last_heartbeat is None:
            status = "unknown"
        else:
            status = "offline"

        return {
            "deviceOnline": self._device_online,
            "lastHeartbeat": last_heartbeat_str,
            "mqttConnected": self._connected,
            "status": status,
        }

    def reset_device_status(self):
        self._last_heartbeat = None
        self._last_device_state = None
        self._device_online = False

    def ensure_connected(self):
        if self._connected:
            return {"success": True, "message": "Already connected"}
        self._log_manager.log_info("MQTT 未连接，正在尝试重连...")
        return self.reconnect()

    def reconnect(self):
        self._log_manager.log_info("开始重新连接 MQTT...")
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
        self._connected = False
        self._subscribed_topics.clear()
        result = self.connect()
        if result["success"]:
            self._subscribe_device_status_topic()
            self._log_manager.log_info("MQTT 重连成功")
        else:
            self._log_manager.log_error(f"MQTT 重连失败: {result['message']}")
        return result

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
                if result["success"] and not self._connected:
                    self._log_manager.log_info("测试连接成功，正在重连实际客户端...")
                    self.ensure_connected()
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
                self._log_manager.log_error("订阅失败: MQTT 未连接")
                return {"success": False, "message": "Not connected to MQTT broker"}
            result = self._client.subscribe(topic)
            if result[0] == 0:
                self._subscribed_topics.add(topic)
                self._log_manager.log_info(f"已订阅主题: {topic}")
                return {"success": True, "message": f"Subscribed to {topic}"}
            else:
                self._log_manager.log_error(f"订阅失败: {topic}, 错误码: {result[0]}")
                return {"success": False, "message": f"Subscribe failed with code: {result[0]}"}
        except Exception as e:
            self._log_manager.log_error(f"订阅异常: {str(e)}")
            return {"success": False, "message": str(e)}

    def unsubscribe_topic(self, topic):
        try:
            if not self._client or not self._connected:
                return {"success": False, "message": "Not connected to MQTT broker"}
            result = self._client.unsubscribe(topic)
            if result[0] == 0:
                self._subscribed_topics.discard(topic)
                self._log_manager.log_info(f"已取消订阅: {topic}")
                return {"success": True, "message": f"Unsubscribed from {topic}"}
            else:
                self._log_manager.log_error(f"取消订阅失败: {topic}, 错误码: {result[0]}")
                return {"success": False, "message": f"Unsubscribe failed with code: {result[0]}"}
        except Exception as e:
            self._log_manager.log_error(f"取消订阅异常: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_subscribed_topics(self):
        return list(self._subscribed_topics)

    def publish_open_door(self):
        try:
            if not self._client or not self._connected:
                self._log_manager.log_info("开门命令检测到未连接，尝试自动重连...")
                reconnect_result = self.ensure_connected()
                if not reconnect_result["success"]:
                    self._log_manager.log_error(f"开门命令失败: 自动重连失败 - {reconnect_result['message']}")
                    return {"success": False, "message": f"Not connected: {reconnect_result['message']}"}
                time.sleep(0.5)
            if not self._client or not self._connected:
                self._log_manager.log_error("开门命令失败: MQTT 未连接")
                return {"success": False, "message": "Not connected to MQTT broker"}
            config = self._config_manager.get_config()
            topic = config.get("doorTopic", "door/00094E53")
            open_angle = config.get("openAngle", 90)
            open_duration = config.get("openDuration", 200)
            close_angle = config.get("closeAngle", 0)
            close_duration = config.get("closeDuration", 200)
            command_payload = json.dumps([
                {"angle": open_angle, "duration": open_duration},
                {"angle": close_angle, "duration": close_duration},
            ])
            self._log_manager.log_send(topic, command_payload)
            result = self._client.publish(topic, command_payload)
            result.wait_for_publish()
            if result.is_published():
                self._log_manager.log_info(f"开门命令发送成功 → {topic}")
                return {"success": True, "message": "Door open command sent"}
            else:
                self._log_manager.log_error("开门命令发送失败")
                return {"success": False, "message": "Failed to publish door open command"}
        except Exception as e:
            self._log_manager.log_error(f"开门命令异常: {str(e)}")
            return {"success": False, "message": str(e)}

    def reload_config(self):
        try:
            self._log_manager.log_info("开始重载 MQTT 配置...")
            was_connected = self._connected
            if was_connected:
                self._log_manager.log_info("断开当前 MQTT 连接")
                self.disconnect()
            self._config_manager.load_config()
            config = self._config_manager.get_config()
            self._log_manager.log_info(f"新配置: {config['mqttServer']}:{config['mqttPort']}")
            self._log_manager.log_info("使用新配置重连 MQTT")
            result = self.connect()
            if result["success"]:
                self._log_manager.log_info("MQTT 配置重载并连接成功")
                return {"success": True, "message": "Config reloaded and connected"}
            else:
                self._log_manager.log_error(f"MQTT 配置重载但连接失败: {result['message']}")
                return {
                    "success": False,
                    "message": f"Config reloaded but connection failed: {result['message']}",
                }
        except Exception as e:
            self._log_manager.log_error(f"配置重载异常: {str(e)}")
            return {"success": False, "message": str(e)}
