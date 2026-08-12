#pragma once

#include <Arduino.h>

#include <vector>

enum class MqttCmdType
{
  Unknown,
  Init,
  Rotate,
};

struct ServoInitConfig
{
  uint8_t pin;
  int minAngle;
  int maxAngle;
  int initialAngle;
};

struct DoorCommand
{
  int angle;
  int duration;
};

struct DoorCommandMessage
{
  MqttCmdType type;
  ServoInitConfig initConfig;
  std::vector<DoorCommand> commands;
};

DoorCommandMessage parseDoorCommandMessage(const byte *payload, unsigned int length);

// Legacy: parse old array format (for backward compatibility)
std::vector<DoorCommand> parseDoorCommands(const byte *payload, unsigned int length);
