#pragma once

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#include "servo_controller.h"

class DoorClickerApp
{
public:
  void setup();
  void loop();

private:
  static void onMqttMessage(char *topic, byte *payload, unsigned int length);

  void setupWifi();
  bool tryConnectMqtt();
  void handleMqttMessage(char *topic, byte *payload, unsigned int length);

  static DoorClickerApp *instance_;

  WiFiClient wifiClient_;
  PubSubClient mqttClient_;
  ServoController servoController_;

  String mqttClientId_;
  String mqttTopic_;

  unsigned long lastMqttAttemptMs_ = 0;
  static constexpr unsigned long kMqttRetryIntervalMs = 5000;
};