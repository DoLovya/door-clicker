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

DoorClickerApp* DoorClickerApp::instance()
{
  return instance_;
}

void DoorClickerApp::setup()
{
  instance_ = this;

  const auto &cfg = ConfigStore::instance().getConfig();

  uint32_t chipId = ESP.getChipId();
  char chipBuf[16];
  snprintf(chipBuf, sizeof(chipBuf), "%08X", chipId);
  mqttClientId_ = String("door_") + chipBuf;
  mqttTopic_ = String("door/") + chipBuf;

  Logger::info(kLogTagBoot, "wifiSsid", cfg.wifiSsid);
  Logger::info(kLogTagBoot, "mqttServer", cfg.mqttServer);
  Logger::info(kLogTagBoot, "mqttPort", cfg.mqttPort);
  Logger::info(kLogTagBoot, "mqttClientId", mqttClientId_);
  Logger::info(kLogTagBoot, "mqttTopic", mqttTopic_);

  Logger::info(kLogTagBoot, "Door Clicker booting");

  setupWifi();

  if (cfg.mqttServer != nullptr && cfg.mqttServer[0] != '\0')
  {
    mqttClient_.setClient(wifiClient_);
    mqttClient_.setBufferSize(256);
    mqttClient_.setServer(cfg.mqttServer, cfg.mqttPort);
    mqttClient_.setCallback(onMqttMessage);
  }
  else
  {
    Logger::warn(kLogTagMqtt, "MQTT server not configured, skip MQTT init");
    Logger::warn(kLogTagMqtt, "Set mqttServer via /config");
  }
}

void DoorClickerApp::loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    unsigned long now = millis();
    if (now - lastWifiAttemptMs_ >= kWifiRetryIntervalMs)
    {
      lastWifiAttemptMs_ = now;
      if (tryConnectWifi())
      {
        lastMqttAttemptMs_ = 0;
      }
    }
    return;
  }

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

  Logger::info(kLogTagWifi, "ssid", cfg.wifiSsid);
  char pwdLenBuf[16];
  snprintf(pwdLenBuf, sizeof(pwdLenBuf), "%d", cfg.wifiPassword ? (int)strlen(cfg.wifiPassword) : 0);
  Logger::info(kLogTagWifi, "password length", pwdLenBuf);

  // Ensure STA mode is ready
  WiFi.mode(WIFI_AP_STA);
  WiFi.disconnect();
  delay(200);
  WiFi.begin(cfg.wifiSsid, cfg.wifiPassword);
  Logger::info(kLogTagWifi, "Starting WiFi connection...");

  unsigned int attempt = 0;
  const unsigned int kMaxAttempts = 40;
  wl_status_t lastStatus = WL_IDLE_STATUS;
  while (WiFi.status() != WL_CONNECTED && attempt < kMaxAttempts)
  {
    delay(250);
    ++attempt;
    wl_status_t st = WiFi.status();
    if (st != lastStatus)
    {
      char logBuf[64];
      snprintf(logBuf, sizeof(logBuf), "attempt %d status=%s", attempt, wifiStatusToString(st).c_str());
      Logger::info(kLogTagWifi, logBuf);
      lastStatus = st;
    }
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Logger::info(kLogTagWifi, "Connected to WiFi");
    String staIp = WiFi.localIP().toString();
    Logger::info(kLogTagWifi, "Station IP", staIp);
    char urlBuf[64];
    snprintf(urlBuf, sizeof(urlBuf), "Visit http://%s/config to configure", staIp.c_str());
    Logger::info(kLogTagWifi, urlBuf);
    Logger::info(kLogTagWifi, "AP also available: http://192.168.4.1/config");
  }
  else
  {
    char errBuf[64];
    snprintf(errBuf, sizeof(errBuf), "WiFi connect failed, status=%s", wifiStatusToString(WiFi.status()).c_str());
    Logger::error(kLogTagWifi, errBuf);

    // Dump scan results to help debug
    Logger::info(kLogTagWifi, "Scanning for networks...");
    int n = WiFi.scanNetworks();
    if (n > 0)
    {
      for (int i = 0; i < n; ++i)
      {
        String scanSsid = WiFi.SSID(i);
        char scanBuf[64];
        snprintf(scanBuf, sizeof(scanBuf), "scan %d: %s rssi=%d", i, scanSsid.c_str(), WiFi.RSSI(i));
        Logger::info(kLogTagWifi, scanBuf);
      }
      WiFi.scanDelete();
    }
    else
    {
      Logger::warn(kLogTagWifi, "No networks found in scan");
    }

    Logger::info(kLogTagWifi, "AP mode still available at http://192.168.4.1/config");
  }
}

bool DoorClickerApp::tryConnectWifi()
{
  const auto &cfg = ConfigStore::instance().getConfig();

  if (cfg.wifiSsid == nullptr || cfg.wifiSsid[0] == '\0')
  {
    return false;
  }

  Logger::info(kLogTagWifi, "WiFi disconnected, attempting reconnect...");
  Logger::info(kLogTagWifi, "ssid", cfg.wifiSsid);

  WiFi.disconnect();
  WiFi.mode(WIFI_AP_STA);
  delay(200);
  WiFi.begin(cfg.wifiSsid, cfg.wifiPassword);

  unsigned int attempt = 0;
  const unsigned int kMaxAttempts = 40;

  while (WiFi.status() != WL_CONNECTED && attempt < kMaxAttempts)
  {
    delay(250);
    ++attempt;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Logger::info(kLogTagWifi, "Reconnected to WiFi");
    String staIp = WiFi.localIP().toString();
    Logger::info(kLogTagWifi, "Station IP", staIp);
    char urlBuf[64];
    snprintf(urlBuf, sizeof(urlBuf), "Visit http://%s/config to configure", staIp.c_str());
    Logger::info(kLogTagWifi, urlBuf);
    Logger::info(kLogTagWifi, "AP also available: http://192.168.4.1/config");
    return true;
  }
  else
  {
    char errBuf[64];
    snprintf(errBuf, sizeof(errBuf), "Reconnect failed, status=%s",
             wifiStatusToString(WiFi.status()).c_str());
    Logger::error(kLogTagWifi, errBuf);
    return false;
  }
}

bool DoorClickerApp::tryConnectMqtt()
{
  const auto &cfg = ConfigStore::instance().getConfig();

  if (cfg.mqttServer == nullptr || cfg.mqttServer[0] == '\0')
  {
    Logger::warn(kLogTagMqtt, "MQTT server not configured, skip connection");
    return false;
  }

  if (!mqttClient_.connected())
  {
    char logBuf[128];
    snprintf(logBuf, sizeof(logBuf), "Connecting to broker %s:%d",
             cfg.mqttServer, cfg.mqttPort);
    Logger::info(kLogTagMqtt, logBuf);
    Logger::info(kLogTagMqtt, "clientId", mqttClientId_);
  }

  const char* user = (cfg.mqttUsername && cfg.mqttUsername[0] != '\0') ? cfg.mqttUsername : nullptr;
  const char* pass = (cfg.mqttPassword && cfg.mqttPassword[0] != '\0') ? cfg.mqttPassword : nullptr;

  if (mqttClient_.connect(mqttClientId_.c_str(), user, pass))
  {
    Logger::info(kLogTagMqtt, "MQTT connected");
    mqttClient_.subscribe(mqttTopic_.c_str());
    Logger::info(kLogTagMqtt, "subscribed topic", mqttTopic_);
    return true;
  }
  else
  {
    char logBuf[64];
    snprintf(logBuf, sizeof(logBuf), "Connect failed, state=%s (%d)",
             mqttStateToString(mqttClient_.state()).c_str(), mqttClient_.state());
    Logger::error(kLogTagMqtt, logBuf);
    return false;
  }
}

void DoorClickerApp::handleMqttMessage(char *topic, byte *payload, unsigned int length)
{
  Logger::info(kLogTagCmd, "topic", topic);
  Logger::info(kLogTagCmd, "payload_length", static_cast<int>(length));

  const DoorCommandMessage msg = parseDoorCommandMessage(payload, length);

  if (msg.type == MqttCmdType::Init)
  {
    servoController_.init(
        msg.initConfig.pin,
        msg.initConfig.minAngle,
        msg.initConfig.maxAngle,
        msg.initConfig.initialAngle);
  }
  else if (msg.type == MqttCmdType::Rotate)
  {
    servoController_.execute(msg.commands);
  }
}