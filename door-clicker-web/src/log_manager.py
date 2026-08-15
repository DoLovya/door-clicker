import os
import time
import json
import threading
from collections import deque


class LogManager:
    _instance = None
    _lock = threading.Lock()

    LOG_TYPE_INFO = "info"
    LOG_TYPE_SEND = "send"
    LOG_TYPE_RECEIVE = "receive"
    LOG_TYPE_ERROR = "error"

    _MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    _BACKUP_COUNT = 5

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._logs = deque(maxlen=500)
        self._log_lock = threading.Lock()
        self._log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "logs")
        self._log_file = os.path.join(self._log_dir, "door_clicker.log")
        self._file_lock = threading.Lock()
        self._init_log_dir()

    def _init_log_dir(self):
        try:
            os.makedirs(self._log_dir, exist_ok=True)
        except Exception:
            pass

    def _write_to_file(self, entry):
        try:
            with self._file_lock:
                log_path = self._log_file
                if os.path.exists(log_path):
                    if os.path.getsize(log_path) >= self._MAX_LOG_FILE_SIZE:
                        self._rotate_logs()
                log_line = json.dumps(entry, ensure_ascii=False) + "\n"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(log_line)
        except Exception:
            pass

    def _rotate_logs(self):
        try:
            for i in range(self._BACKUP_COUNT - 1, 0, -1):
                src = f"{self._log_file}.{i}"
                dst = f"{self._log_file}.{i + 1}"
                if os.path.exists(src):
                    os.rename(src, dst)
            if os.path.exists(self._log_file):
                os.rename(self._log_file, f"{self._log_file}.1")
        except Exception:
            pass

    def add_log(self, log_type, message, topic=None, payload=None):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "type": log_type,
            "message": message,
            "topic": topic,
            "payload": payload,
        }
        with self._log_lock:
            self._logs.append(entry)
        self._write_to_file(entry)

    def log_info(self, message):
        self.add_log(self.LOG_TYPE_INFO, message)

    def log_send(self, topic, payload):
        self.add_log(self.LOG_TYPE_SEND, f"发送到 [{topic}]", topic, payload)

    def log_receive(self, topic, payload):
        self.add_log(self.LOG_TYPE_RECEIVE, f"收到 [{topic}]", topic, payload)

    def log_error(self, message):
        self.add_log(self.LOG_TYPE_ERROR, message)

    def get_logs(self, log_type=None, limit=None):
        with self._log_lock:
            logs = list(self._logs)
        if log_type:
            logs = [log for log in logs if log["type"] == log_type]
        if limit:
            logs = logs[-limit:]
        return logs

    def clear_logs(self):
        with self._log_lock:
            self._logs.clear()

    def get_log_file_path(self):
        return self._log_file

    def read_log_file(self, lines=200):
        try:
            if not os.path.exists(self._log_file):
                return []
            with open(self._log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            recent = all_lines[-lines:]
            result = []
            for line in recent:
                try:
                    result.append(json.loads(line.strip()))
                except Exception:
                    pass
            return result
        except Exception:
            return []
