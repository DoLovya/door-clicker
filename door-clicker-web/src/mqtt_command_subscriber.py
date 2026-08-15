# subscriber.py
import paho.mqtt.client as mqtt


# 定义连接回调函数
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # 连接成功后订阅主题
    client.subscribe("data")


# 定义消息接收回调函数
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")


# 创建 MQTT 客户端
client = mqtt.Client()

# 设置连接回调函数和消息回调函数
client.on_connect = on_connect
client.on_message = on_message

# 连接到 MQTT 服务器
client.connect("127.0.0.1", 1883, 60)

# 启动客户端
client.loop_forever()
