import logging
import os
import sys

from flask import Flask, jsonify, render_template, request

from config_manager import ConfigManager
from mqtt_client_manager import MqttClientManager
from log_manager import LogManager
from auth import init_auth, login_required

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

config_manager = None
mqtt_client_manager = None
log_manager = None
init_mqtt = None
app = None


def create_app():
    global config_manager, mqtt_client_manager, log_manager, init_mqtt, app

    config_manager = ConfigManager()
    mqtt_client_manager = MqttClientManager()
    log_manager = LogManager()

    _app = Flask(__name__, template_folder='templates', static_folder='static')
    app = _app

    init_auth(_app, config_manager)

    @_app.errorhandler(400)
    def bad_request(error):
        log_manager.log_error(f"400 Bad Request: {request.path} - {request.get_data(as_text=True)}")
        return jsonify({"error": "Bad Request"}), 400

    @_app.errorhandler(404)
    def not_found(error):
        log_manager.log_error(f"404 Not Found: {request.path}")
        return jsonify({"error": "Not Found"}), 404

    @_app.errorhandler(500)
    def internal_server_error(error):
        log_manager.log_error(f"500 Internal Server Error: {request.path} - {str(error)}")
        return jsonify({"error": "Internal Server Error"}), 500

    def _init_mqtt():
        logger.info("Initializing MQTT connection...")
        log_manager.log_info("正在初始化 MQTT 连接...")
        config = config_manager.get_config()
        logger.info("MQTT Server: %s:%d", config["mqttServer"], config["mqttPort"])

        result = mqtt_client_manager.connect()
        if result["success"]:
            logger.info("MQTT connected successfully")
            log_manager.log_info(f"MQTT 连接成功 {config['mqttServer']}:{config['mqttPort']}")
        else:
            logger.warning("MQTT connection failed: %s", result["message"])
            log_manager.log_error(f"MQTT 连接失败: {result['message']}")

    init_mqtt = _init_mqtt

    @_app.route("/")
    def index():
        return render_template("door.html")

    @_app.route("/config")
    @login_required
    def config_page():
        return render_template("index.html")

    @_app.route("/api/open/door", methods=["POST"])
    def api_open_door():
        log_manager.log_info("收到开门请求")
        result = mqtt_client_manager.publish_open_door()
        if result["success"]:
            log_manager.log_info("开门指令发送成功")
            config = config_manager.get_config()
            return jsonify([
                {"angle": config.get("openAngle", 90), "duration": config.get("openDuration", 200)},
                {"angle": config.get("closeAngle", 0), "duration": config.get("closeDuration", 200)},
            ])
        log_manager.log_error(f"开门指令发送失败: {result['message']}")
        return jsonify({"error": result["message"]}), 500

    @_app.route("/api/config", methods=["GET"])
    @login_required
    def api_get_config():
        config = config_manager.get_config()
        safe_config = {k: v for k, v in config.items() if k not in ("adminPasswordHash",)}
        safe_config["mqttPassword"] = "***" if config.get("mqttPassword") else ""
        return jsonify(safe_config)

    @_app.route("/api/config", methods=["PUT"])
    @login_required
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

        for angle_field in ("openAngle", "closeAngle"):
            if angle_field in data:
                val = data[angle_field]
                if not isinstance(val, int) or isinstance(val, bool):
                    return jsonify({"error": f"{angle_field} must be an integer"}), 400
                if val < 0 or val > 180:
                    return jsonify({"error": f"{angle_field} must be between 0 and 180"}), 400

        for duration_field in ("openDuration", "closeDuration"):
            if duration_field in data:
                val = data[duration_field]
                if not isinstance(val, int) or isinstance(val, bool):
                    return jsonify({"error": f"{duration_field} must be an integer"}), 400
                if val < 50 or val > 10000:
                    return jsonify({"error": f"{duration_field} must be between 50 and 10000"}), 400

        if "adminPassword" in data:
            import hashlib
            new_hash = hashlib.sha256(data["adminPassword"].encode("utf-8")).hexdigest()
            data["adminPasswordHash"] = new_hash
            del data["adminPassword"]
            log_manager.log_info("管理员密码已修改")

        config = config_manager.update_config(data)
        log_manager.log_info(
            f"配置已更新: mqttServer={data.get('mqttServer', '未变')}, "
            f"doorTopic={data.get('doorTopic', '未变')}"
        )

        reload_result = mqtt_client_manager.reload_config()
        reload_status = "成功" if reload_result["success"] else (
            "失败 - " + reload_result["message"]
        )
        log_manager.log_info(f"MQTT 配置重载: {reload_status}")

        return jsonify({
            "config": config,
            "reload": reload_result,
        })

    @_app.route("/api/mqtt/test", methods=["POST"])
    @login_required
    def api_test_mqtt():
        log_manager.log_info("测试 MQTT 连接...")
        result = mqtt_client_manager.test_connection()
        if result["success"]:
            log_manager.log_info("MQTT 连接测试成功")
        else:
            log_manager.log_error(f"MQTT 连接测试失败: {result['message']}")
        return jsonify(result)

    @_app.route("/api/mqtt/reconnect", methods=["POST"])
    @login_required
    def api_reconnect_mqtt():
        log_manager.log_info("手动触发 MQTT 重连...")
        result = mqtt_client_manager.reconnect()
        if result["success"]:
            log_manager.log_info("MQTT 重连成功")
        else:
            log_manager.log_error(f"MQTT 重连失败: {result['message']}")
        return jsonify(result)

    @_app.route("/api/mqtt/status", methods=["GET"])
    def api_mqtt_status():
        device_status = mqtt_client_manager.get_device_status()
        return jsonify({
            "connected": mqtt_client_manager.is_connected(),
            "deviceOnline": device_status["deviceOnline"],
            "deviceStatus": device_status["status"],
            "lastHeartbeat": device_status["lastHeartbeat"],
        })

    @_app.route("/api/device/status", methods=["GET"])
    def api_device_status():
        status = mqtt_client_manager.get_device_status()
        return jsonify(status)

    @_app.route("/api/device/reset", methods=["POST"])
    @login_required
    def api_reset_device_status():
        mqtt_client_manager.reset_device_status()
        log_manager.log_info("手动重置设备状态")
        return jsonify({"success": True, "message": "设备状态已重置"})

    @_app.route("/api/topics", methods=["GET"])
    @login_required
    def api_get_topics():
        topics = mqtt_client_manager.get_subscribed_topics()
        return jsonify(topics)

    @_app.route("/api/topics", methods=["POST"])
    @login_required
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

    @_app.route("/api/topics/<path:topic>", methods=["DELETE"])
    @login_required
    def api_delete_topic(topic):
        result = mqtt_client_manager.unsubscribe_topic(topic)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400

    @_app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify({"status": "ok"})

    @_app.route("/api/logs", methods=["GET"])
    @login_required
    def api_get_logs():
        log_type = request.args.get("type")
        limit = request.args.get("limit", type=int)
        logs = log_manager.get_logs(log_type=log_type, limit=limit)
        return jsonify(logs)

    @_app.route("/api/logs", methods=["DELETE"])
    @login_required
    def api_clear_logs():
        log_manager.clear_logs()
        log_manager.log_info("日志已清空")
        return jsonify({"success": True, "message": "日志已清空"})

    _app.config_manager = config_manager
    _app.mqtt_client_manager = mqtt_client_manager
    _app.log_manager = log_manager
    _app.init_mqtt = init_mqtt

    return _app


if app is None:
    app = create_app()


if __name__ == "__main__":
    logger.info("Starting Door Clicker Web server...")
    log_manager.log_info("=" * 50)
    log_manager.log_info("Door Clicker Web 服务启动")
    log_manager.log_info(f"日志文件路径: {log_manager.get_log_file_path()}")
    log_manager.log_info("=" * 50)
    init_mqtt()
    port = int(os.environ.get("PORT", "5001"))
    logger.info(f"Server running on http://0.0.0.0:{port}")
    log_manager.log_info(f"Web 服务已启动，监听端口 {port}")
    app.run(host="0.0.0.0", port=port)
