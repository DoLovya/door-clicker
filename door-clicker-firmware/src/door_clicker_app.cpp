#include "door_clicker_app.h"

#include "config_store.h"
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

void DoorClickerApp::setup()
{
  instance_ = this;

  const auto &cfg = ConfigStore::instance().getConfig();

  Logger::info(kLogTagBoot, "servoPin", cfg.servoPin);
  Logger::info(kLogTagBoot, "wifiSsid", cfg.wifiSsid);
  Logger::info(kLogTagBoot, "mqttServer", cfg.mqttServer);
  Logger::info(kLogTagBoot, "mqttPort", cfg.mqttPort);
  Logger::info(kLogTagBoot, "mqttClientId", cfg.mqttClientId);

  Logger::info(kLogTagBoot, "Door Clicker booting");
  servoController_.begin(cfg.servoPin);

  setupWifi();

  if (cfg.mqttServer != nullptr && cfg.mqttServer[0] != '\0' &&
      cfg.mqttClientId != nullptr && cfg.mqttClientId[0] != '\0')
  {
    mqttClient_.setServer(cfg.mqttServer, cfg.mqttPort);
    mqttClient_.setCallback(onMqttMessage);
  }
  else
  {
    Logger::warn(kLogTagMqtt, "MQTT config incomplete, skip MQTT init");
    Logger::warn(kLogTagMqtt, "Set mqttServer and mqttClientId via /config");
  }
}

void DoorClickerApp::loop()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    if (!mqttClient_.connected())
    {
      unsigned long now = millis();
      if (now - lastMqttAttemptMs_ >= kMqttRetryIntervalMs)
      {
        lastMqttAttemptMs_ = now;
        tryConnectMqtt();
      }
    }
    else
    {
      mqttClient_.loop();
    }
  }
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
  const auto &cfg = ConfigStore::instance().getConfig();

  if (cfg.wifiSsid == nullptr || cfg.wifiSsid[0] == '\0')
  {
    Logger::warn(kLogTagWifi, "No WiFi SSID configured, AP mode only");
    Logger::info(kLogTagWifi, "Connect to AP and visit /config to set WiFi");
    return;
  }

  delay(10);
  Logger::info(kLogTagWifi, "ssid", cfg.wifiSsid);
  Logger::info(kLogTagWifi, "Starting WiFi connection");

  WiFi.begin(cfg.wifiSsid, cfg.wifiPassword);

  unsigned int attempt = 0;
  const unsigned int kMaxAttempts = 20;
  while (WiFi.status() != WL_CONNECTED && attempt < kMaxAttempts)
  {
    delay(250);
    ++attempt;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Logger::info(kLogTagWifi, "Connected to WiFi");
    Logger::info(kLogTagWifi, "ip", WiFi.localIP().toString());
  }
  else
  {
    Logger::error(kLogTagWifi, "WiFi connect failed, AP mode still available");
  }
}

bool DoorClickerApp::tryConnectMqtt()
{
  const auto &cfg = ConfigStore::instance().getConfig();

  if (cfg.mqttServer == nullptr || cfg.mqttServer[0] == '\0' ||
      cfg.mqttClientId == nullptr || cfg.mqttClientId[0] == '\0')
  {
    Logger::warn(kLogTagMqtt, "MQTT not configured, skip connection");
    return false;
  }

  Logger::info(
      kLogTagMqtt,
      String("Connecting to broker ") + cfg.mqttServer + ":" + cfg.mqttPort);

  if (mqttClient_.connect(cfg.mqttClientId))
  {
    Logger::info(kLogTagMqtt, "MQTT connected");
    mqttClient_.subscribe(cfg.mqttTopic);
    Logger::info(kLogTagMqtt, "topic", cfg.mqttTopic);
    return true;
  }
  else
  {
    Logger::error(
        kLogTagMqtt,
        String("Connect failed, state=") + mqttStateToString(mqttClient_.state()) + " (" +
            mqttClient_.state() + ")");
    return false;
  }
}

void DoorClickerApp::handleMqttMessage(char *topic, byte *payload, unsigned int length)
{
  Logger::info(kLogTagCmd, "topic", topic);
  Logger::info(kLogTagCmd, "payload_length", static_cast<int>(length));

  const std::vector<DoorCommand> commands = parseDoorCommands(payload, length);
  servoController_.execute(commands);
}