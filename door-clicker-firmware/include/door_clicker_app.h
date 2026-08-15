#pragma once

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#include "servo_controller.h"

class DoorClickerApp
{
public:
  void setup();
  void loop();

  static DoorClickerApp* instance();
  ServoController& getServoController() { return servoController_; }

private:
  static void onMqttMessage(char *topic, byte *payload, unsigned int length);

  void setupWifi();
  bool tryConnectWifi();
  bool tryConnectMqtt();
  void handleMqttMessage(char *topic, byte *payload, unsigned int length);

  void publishHeartbeat();
  void publishConnectedEvent();

  static DoorClickerApp *instance_;

  WiFiClient wifiClient_;
  PubSubClient mqttClient_;
  ServoController servoController_;

  String mqttClientId_;
  String mqttTopic_;
  String mqttStatusTopic_;

  unsigned long lastWifiAttemptMs_ = 0;
  unsigned long lastMqttAttemptMs_ = 0;
  unsigned long lastHeartbeatMs_ = 0;
  static constexpr unsigned long kWifiRetryIntervalMs = 5000;
  static constexpr unsigned long kMqttRetryIntervalMs = 5000;
  static constexpr unsigned long kHeartbeatIntervalMs = 30000;
};