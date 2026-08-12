#include "servo_controller.h"

#include "logger.h"

namespace
{
const char *kLogTagServo = "SERVO";
} // namespace

int ServoController::clampAngle(int angle) const
{
  if (angle < minAngle_) return minAngle_;
  if (angle > maxAngle_) return maxAngle_;
  return angle;
}

void ServoController::begin(uint8_t pin, int initialAngle)
{
  init(pin, 0, 180, initialAngle);
}

void ServoController::init(uint8_t pin, int minAngle, int maxAngle, int initialAngle)
{
  if (initialized_)
  {
    servo_.detach();
  }

  pin_ = pin;
  minAngle_ = minAngle;
  maxAngle_ = maxAngle;

  initialAngle = clampAngle(initialAngle);
  currentAngle_ = initialAngle;

  servo_.attach(pin_);
  servo_.write(initialAngle);
  initialized_ = true;

  Logger::info(kLogTagServo, String("Initialized, pin=") + pin_ +
                                " range=" + minAngle_ + "-" + maxAngle_ +
                                " angle=" + initialAngle);
}

void ServoController::execute(const std::vector<DoorCommand> &commands)
{
  if (!initialized_)
  {
    Logger::warn(kLogTagServo, "Servo not initialized, skip execute");
    return;
  }

  if (commands.empty())
  {
    Logger::warn(kLogTagServo, "No commands to execute");
    return;
  }

  for (size_t index = 0; index < commands.size(); ++index)
  {
    const DoorCommand &command = commands[index];
    int angle = clampAngle(command.angle);
    currentAngle_ = angle;

    char logBuf[64];
    snprintf(logBuf, sizeof(logBuf), "Step %d/%d angle=%d duration=%dms",
             (int)(index + 1), (int)commands.size(), angle, command.duration);
    Logger::info(kLogTagServo, logBuf);

    servo_.write(angle);
    delay(command.duration);
  }

  Logger::info(kLogTagServo, "Command execution finished");
}
