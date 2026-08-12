#pragma once

#include <Arduino.h>
#include <Servo.h>

#include <vector>

#include "door_command.h"

class ServoController
{
public:
  ServoController() = default;

  void begin(uint8_t pin, int initialAngle = 0);
  void execute(const std::vector<DoorCommand> &commands);

private:
  uint8_t pin_ = 0;
  Servo servo_;
};
