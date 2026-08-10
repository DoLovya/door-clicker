#include "door_clicker_app.h"

#include "app_config.h"
#include "door_command.h"
#include "logger.h"

DoorClickerApp *DoorClickerApp::instance_ = nullptr;

namespace
{
const char *kLogTagBoot = "BOOT";
const char *kLogTagWifi = "WIFI";
const char *kLogTagMqtt = "MQTT";
const char *kLogTagCmd = "CMD";

String wifiStatusToString(wl_status_t status)
{
  switch (status)
  {
  case WL_IDLE_STATUS:
    return "IDLE";
  case WL_NO_SSID_AVAIL:
    return "NO_SSID";
  case WL_SCAN_COMPLETED:
    return "SCAN_COMPLETED";
  case WL_CONNECTED:
    return "CONNECTED";
  case WL_CONNECT_FAILED:
    return "CONNECT_FAILED";
  case WL_CONNECTION_LOST:
    return "CONNECTION_LOST";
  case WL_DISCONNECTED:
    return "DISCONNECTED";
  case WL_WRONG_PASSWORD:
    return "WRONG_PASSWORD";
  default:
    return "UNKNOWN";
  }
}

String mqttStateToString(int state)
{
  switch (state)
  {
  case MQTT_CONNECTION_TIMEOUT:
    return "CONNECTION_TIMEOUT";
  case MQTT_CONNECTION_LOST:
    return "CONNECTION_LOST";
  case MQTT_CONNECT_FAILED:
    return "CONNECT_FAILED";
  case MQTT_DISCONNECTED:
    return "DISCONNECTED";
  case MQTT_CONNECTED:
    return "CONNECTED";
  case MQTT_CONNECT_BAD_PROTOCOL:
    return "BAD_PROTOCOL";
  case MQTT_CONNECT_BAD_CLIENT_ID:
    return "BAD_CLIENT_ID";
  case MQTT_CONNECT_UNAVAILABLE:
    return "UNAVAILABLE";
  case MQTT_CONNECT_BAD_CREDENTIALS:
    return "BAD_CREDENTIALS";
  case MQTT_CONNECT_UNAUTHORIZED:
    return "UNAUTHORIZED";
  default:
    return "UNKNOWN";
  }
}
} // namespace

DoorClickerApp::DoorClickerApp()
  : mqttClient_(wifiClient_),
    servoController_(AppConfig::kServoPin)
{
}

void DoorClickerApp::setup()
{
  instance_ = this;

  pinMode(AppConfig::kLedPin, OUTPUT);
  Logger::begin(AppConfig::kSerialBaudRate);
  Logger::info(kLogTagBoot, "Door Clicker booting");
  Logger::info(kLogTagBoot, "serial_baud_rate", AppConfig::kSerialBaudRate);
  servoController_.begin();

  setupWifi();

  mqttClient_.setServer(AppConfig::kMqttServer, AppConfig::kMqttPort);
  mqttClient_.setCallback(onMqttMessage);
}

void DoorClickerApp::loop()
{
  if (!mqttClient_.connected())
  {
    reconnectMqtt();
  }

  mqttClient_.loop();
}

void DoorClickerApp::onMqttMessage(char *topic, byte *payload, unsigned int length)
{
  if (instance_ != nullptr)
  {
    instance_->handleMqttMessage(topic, payload, length);
  }
}

void DoorClickerApp::setupWifi()
{
  delay(10);
  Logger::info(kLogTagWifi, "ssid", AppConfig::kWifiSsid);
  Logger::info(kLogTagWifi, "Starting WiFi connection");

  WiFi.begin(AppConfig::kWifiSsid, AppConfig::kWifiPassword);

  unsigned int attempt = 0;
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    ++attempt;
    Logger::warn(kLogTagWifi,
                 String("Waiting for connection, attempt=") + attempt +
                     ", status=" + wifiStatusToString(WiFi.status()) + " (" +
                     WiFi.status() + ")");
  }

  Logger::info(kLogTagWifi, "Connected to WiFi");
  Logger::info(kLogTagWifi, "ip", WiFi.localIP().toString());
}

void DoorClickerApp::reconnectMqtt()
{
  while (!mqttClient_.connected())
  {
    Logger::info(kLogTagMqtt,
                 String("Connecting to broker ") + AppConfig::kMqttServer +
                     ":" + AppConfig::kMqttPort);

    if (mqttClient_.connect(AppConfig::kMqttClientId))
    {
      Logger::info(kLogTagMqtt, "MQTT connected");
      mqttClient_.subscribe(AppConfig::kMqttTopic);
      Logger::info(kLogTagMqtt, "topic", AppConfig::kMqttTopic);
    }
    else
    {
      Logger::error(kLogTagMqtt,
                    String("Connect failed, state=") +
                        mqttStateToString(mqttClient_.state()) + " (" +
                        mqttClient_.state() + ")");
      Logger::warn(kLogTagMqtt, "Retry in 5 seconds");
      delay(5000);
    }
  }
}

void DoorClickerApp::handleMqttMessage(char *topic, byte *payload, unsigned int length)
{
  Logger::info(kLogTagCmd, "topic", topic);
  Logger::info(kLogTagCmd, "payload_length", static_cast<int>(length));

  const std::vector<DoorCommand> commands = parseDoorCommands(payload, length);
  servoController_.execute(commands);
}
