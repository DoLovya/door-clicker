#pragma once

#include <Arduino.h>
#include <Servo.h>

#include <vector>

#include "door_command.h"

class ServoController
{
public:
  explicit ServoController(uint8_t pin);

  void begin(int initialAngle = 0);
  void execute(const std::vector<DoorCommand> &commands);

private:
  uint8_t pin_;
  Servo servo_;
};
