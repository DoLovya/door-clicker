import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from app import app, init_mqtt

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
_LOGS_DIR = os.path.join(_DATA_DIR, "logs")

os.makedirs(_DATA_DIR, exist_ok=True)
os.makedirs(_LOGS_DIR, exist_ok=True)

if __name__ == "__main__":
    init_mqtt()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
