from flask import Flask, jsonify, render_template

from mqtt_command_publisher import publish_open_door_command

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/open/door", methods=["POST"])
def api_open_door():
    publish_open_door_command()
    return jsonify([{"angle": 90, "duration": 200}, {"angle": 0, "duration": 200}])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
