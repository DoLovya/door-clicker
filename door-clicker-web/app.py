import logging

from flask import Flask, jsonify, render_template, request

from config_manager import ConfigManager
from mqtt_client_manager import MqttClientManager
from log_manager import LogManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request"}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal Server Error"}), 500


config_manager = ConfigManager()
mqtt_client_manager = MqttClientManager()
log_manager = LogManager()


def init_mqtt():
    logger.info("Initializing MQTT connection...")
    config = config_manager.get_config()
    logger.info("MQTT Server: %s:%d", config["mqttServer"], config["mqttPort"])

    result = mqtt_client_manager.connect()
    if result["success"]:
        logger.info("MQTT connected successfully")
    else:
        logger.warning("MQTT connection failed: %s", result["message"])


@app.route("/")
def index():
    return render_template("door.html")


@app.route("/config")
def config_page():
    return render_template("index.html")


@app.route("/api/open/door", methods=["POST"])
def api_open_door():
    result = mqtt_client_manager.publish_open_door()
    if result["success"]:
        return jsonify([{"angle": 90, "duration": 200}, {"angle": 0, "duration": 200}])
    return jsonify({"error": result["message"]}), 500


@app.route("/api/config", methods=["GET"])
def api_get_config():
    config = config_manager.get_config()
    return jsonify(config)


@app.route("/api/config", methods=["PUT"])
def api_update_config():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if "mqttPort" in data:
        port = data["mqttPort"]
        if not isinstance(port, int) or isinstance(port, bool):
            return jsonify({"error": "mqttPort must be an integer"}), 400
        if port < 1 or port > 65535:
            return jsonify({"error": "mqttPort must be between 1 and 65535"}), 400

    if "mqttServer" in data:
        server = data["mqttServer"]
        if not isinstance(server, str):
            return jsonify({"error": "mqttServer must be a string"}), 400
        if not server.strip():
            return jsonify({"error": "mqttServer must be a non-empty string"}), 400

    if "topics" in data:
        if not isinstance(data["topics"], list):
            return jsonify({"error": "Topics must be an array"}), 400

    config = config_manager.update_config(data)
    reload_result = mqtt_client_manager.reload_config()

    return jsonify({
        "config": config,
        "reload": reload_result,
    })


@app.route("/api/mqtt/test", methods=["POST"])
def api_test_mqtt():
    result = mqtt_client_manager.test_connection()
    return jsonify(result)


@app.route("/api/mqtt/status", methods=["GET"])
def api_mqtt_status():
    return jsonify({"connected": mqtt_client_manager.is_connected()})


@app.route("/api/topics", methods=["GET"])
def api_get_topics():
    topics = mqtt_client_manager.get_subscribed_topics()
    return jsonify(topics)


@app.route("/api/topics", methods=["POST"])
def api_add_topic():
    data = request.get_json(silent=True)
    if not data or "topic" not in data:
        return jsonify({"error": "Request body must contain 'topic' field"}), 400

    topic = data["topic"]
    if not isinstance(topic, str):
        return jsonify({"error": "Topic must be a string"}), 400
    if not topic.strip():
        return jsonify({"error": "Topic must be a non-empty string"}), 400

    result = mqtt_client_manager.subscribe_topic(topic)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400


@app.route("/api/topics/<path:topic>", methods=["DELETE"])
def api_delete_topic(topic):
    result = mqtt_client_manager.unsubscribe_topic(topic)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})


@app.route("/api/logs", methods=["GET"])
def api_get_logs():
    log_type = request.args.get("type")
    limit = request.args.get("limit", type=int)
    logs = log_manager.get_logs(log_type=log_type, limit=limit)
    return jsonify(logs)


@app.route("/api/logs", methods=["DELETE"])
def api_clear_logs():
    log_manager.clear_logs()
    return jsonify({"success": True, "message": "日志已清空"})


if __name__ == "__main__":
    logger.info("Starting Door Clicker Web server...")
    init_mqtt()
    logger.info("Server running on http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080)