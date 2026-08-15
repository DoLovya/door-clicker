import json

import paho.mqtt.client as mqtt


def on_connect(client: mqtt.Client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    command_payload = json.dumps(
        [
            {"angle": 60, "duration": 200},
            {"angle": 0, "duration": 200},
        ]
    )
    client.publish("data", command_payload)
    client.disconnect()


def publish_open_door_command():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()
