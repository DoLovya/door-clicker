#pragma once

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#include "servo_controller.h"

class DoorClickerApp
{
public:
  DoorClickerApp();

  void setup();
  void loop();

private:
  static void onMqttMessage(char *topic, byte *payload, unsigned int length);

  void setupWifi();
  void reconnectMqtt();
  void handleMqttMessage(char *topic, byte *payload, unsigned int length);

  static DoorClickerApp *instance_;

  WiFiClient wifiClient_;
  PubSubClient mqttClient_;
  ServoController servoController_;
};
