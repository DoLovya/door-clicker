#pragma once

#include <Arduino.h>

#include <vector>

struct DoorCommand
{
  int angle;
  int duration;
};

std::vector<DoorCommand> parseDoorCommands(const byte *payload, unsigned int length);
