#include "servo_controller.h"

#include "logger.h"

namespace
{
const char *kLogTagServo = "SERVO";
} // namespace

void ServoController::begin(uint8_t pin, int initialAngle)
{
  pin_ = pin;
  servo_.attach(pin_);
  servo_.write(initialAngle);
  Logger::info(kLogTagServo, String("Initialized, pin=") + pin_ + ", angle=" + initialAngle);
}

void ServoController::execute(const std::vector<DoorCommand> &commands)
{
  if (commands.empty())
  {
    Logger::warn(kLogTagServo, "No commands to execute");
    return;
  }

  for (size_t index = 0; index < commands.size(); ++index)
  {
    const DoorCommand &command = commands[index];
    Logger::info(
        kLogTagServo,
        String("Step ") + (index + 1) + "/" + commands.size() + ", angle=" + command.angle +
            ", duration_ms=" + command.duration);
    servo_.write(command.angle);
    delay(command.duration);
  }

  Logger::info(kLogTagServo, "Command execution finished");
}
