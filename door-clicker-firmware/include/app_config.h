#pragma once

namespace AppConfig
{
constexpr int kServoPin = 5;
constexpr int kLedPin = 2;
constexpr long kSerialBaudRate = 19200;

constexpr const char *kWifiSsid = "TP-LINK_2.4G_AB27";
constexpr const char *kWifiPassword = "@wzz032927_";

constexpr const char *kMqttServer = "47.94.198.29";
constexpr int kMqttPort = 1883;
constexpr const char *kMqttTopic = "data";
constexpr const char *kMqttClientId = "ESP8266Client";
} // namespace AppConfig
