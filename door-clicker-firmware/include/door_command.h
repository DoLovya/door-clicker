#pragma once

#include <Arduino.h>

#include <vector>

enum class MqttCmdType
{
  Unknown,
  Rotate,
};

struct DoorCommand
{
  int angle;
  int duration;
};

struct DoorCommandMessage
{
  MqttCmdType type;
  std::vector<DoorCommand> commands;
};

DoorCommandMessage parseDoorCommandMessage(const byte *payload, unsigned int length);

// Legacy: parse old array format (for backward compatibility)
std::vector<DoorCommand> parseDoorCommands(const byte *payload, unsigned int length);