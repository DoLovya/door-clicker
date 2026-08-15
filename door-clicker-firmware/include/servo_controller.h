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
  void init(uint8_t pin, int minAngle = 0, int maxAngle = 180, int initialAngle = 0);
  void execute(const std::vector<DoorCommand> &commands);
  void testOpen();

  uint8_t getPin() const { return pin_; }
  int getMinAngle() const { return minAngle_; }
  int getMaxAngle() const { return maxAngle_; }
  int getCurrentAngle() const { return currentAngle_; }
  bool isInitialized() const { return initialized_; }

private:
  uint8_t pin_ = 0;
  int minAngle_ = 0;
  int maxAngle_ = 180;
  int currentAngle_ = 0;
  bool initialized_ = false;
  Servo servo_;

  int clampAngle(int angle) const;
};