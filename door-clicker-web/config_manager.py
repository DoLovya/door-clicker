import json
import os
import threading
import copy


class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    _DEFAULT_CONFIG = {
        "mqttServer": "127.0.0.1",
        "mqttPort": 1883,
        "mqttUsername": "",
        "mqttPassword": "",
        "topics": [],
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self._config = {}
        self.load_config()

    @staticmethod
    def get_default_config():
        return copy.deepcopy(ConfigManager._DEFAULT_CONFIG)

    def load_config(self):
        with self._lock:
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = {**self._DEFAULT_CONFIG, **data}
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                self._config = copy.deepcopy(self._DEFAULT_CONFIG)
        return self._config

    def save_config(self, config_dict):
        if not isinstance(config_dict, dict):
            return False
        with self._lock:
            try:
                with open(self._config_path, "w", encoding="utf-8") as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                self._config = copy.deepcopy(config_dict)
                return True
            except (OSError, TypeError, ValueError):
                return False

    def get_config(self):
        with self._lock:
            return copy.deepcopy(self._config)

    def update_config(self, partial_dict):
        with self._lock:
            for key, value in partial_dict.items():
                if key in self._DEFAULT_CONFIG:
                    self._config[key] = value
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return copy.deepcopy(self._config)