#include <Servo.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <iostream>
#include <string>

const int servoPin = 5; // 舵机信号线连接的引脚

Servo myServo; // 创建一个 Servo 对象

#define DEBUG

// MQTT 配置
const char *mqtt_server = "47.94.198.29";
const int mqtt_port = 1883;
const char *mqtt_topic = "data";

WiFiClient espClient;
PubSubClient client(espClient);

struct Data
{
  int angle;
  int duration;
};

class Log
{
public:
  static void debug(const std::string &str)
  {
#ifdef DEBUG
    Serial.println(str.c_str());
#endif
  }
  static void debug(int value)
  {
#ifdef DEBUG
    Serial.println(value);
#endif
  }
};

void setup_wifi(const char *ssid, const char *password)
{
  delay(10);
  Log::debug(std::string("Connecting to ") + std::string(ssid));

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Log::debug(".");
  }

  Log::debug("Connected to WiFi");
}

// 连接到 MQTT 服务器
void reconnect()
{
  while (!client.connected())
  {
    Log::debug("Attempting MQTT connection...");
    if (client.connect("ESP8266Client"))
    {
      Log::debug("connected");
      client.subscribe(mqtt_topic); // 订阅主题
    }
    else
    {
      Log::debug("failed, rc=");
      Log::debug(client.state());
      Log::debug("Try again in 5 seconds");
      delay(5000);
    }
  }
}

void click(std::vector<Data> datas)
{
  for (Data data : datas)
  {
    myServo.write(data.angle);
    delay(data.duration);
  }
}

std::vector<Data> parse_payload(const char *json)
{
  Log::debug(json);

  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, json);
  if (error)
  {
    Log::debug("deserializeJson() failed！");
    Log::debug(error.c_str());
    return std::vector<Data>();
  }

  std::vector<Data> datas;
  JsonArray array = doc.as<JsonArray>();
  for (JsonObject obj : array)
  {
    Data data;
    data.angle = obj["angle"].as<int>();
    data.duration = obj["duration"].as<int>();
    datas.push_back(data);
  }
  return datas;
}

// 处理收到的消息
void callback(char *topic, byte *payload, unsigned int length)
{
  Log::debug("Message arrived on topic:");
  Log::debug(topic);
  std::vector<Data> datas = parse_payload((const char *)payload);
  click(datas);
}

#define LED_PIN 2

void setup()
{
  pinMode(LED_PIN, OUTPUT);
#ifdef DEBUG
  Serial.begin(19200);
#endif
  myServo.attach(servoPin);
  myServo.write(0);
  setup_wifi("TP-LINK_2.4G_AB27", "wzz032927@");
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop()
{
  if (!client.connected())
  {
    reconnect();
  }
  client.loop();
}
