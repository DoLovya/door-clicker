import time
import threading
from collections import deque


class LogManager:
    _instance = None
    _lock = threading.Lock()

    LOG_TYPE_INFO = "info"
    LOG_TYPE_SEND = "send"
    LOG_TYPE_RECEIVE = "receive"
    LOG_TYPE_ERROR = "error"

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
