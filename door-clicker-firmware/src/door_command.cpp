#include "door_command.h"

#include <ArduinoJson.h>

#include "logger.h"

namespace
{
const char *kLogTagCmd = "CMD";
}

std::vector<DoorCommand> parseDoorCommands(const byte *payload, unsigned int length)
{
  String message;
  message.reserve(length);

  for (unsigned int index = 0; index < length; ++index)
  {
    message += static_cast<char>(payload[index]);
  }

  Logger::info(kLogTagCmd, "payload", message);

  JsonDocument document;
  DeserializationError error = deserializeJson(document, message);
  if (error)
  {
    Logger::error(kLogTagCmd, "deserializeJson() failed");
    Logger::error(kLogTagCmd, "reason", error.c_str());
    return {};
  }

  std::vector<DoorCommand> commands;
  JsonArray jsonArray = document.as<JsonArray>();

  for (JsonObject object : jsonArray)
  {
    DoorCommand command{};
    command.angle = object["angle"] | 0;
    command.duration = object["duration"] | 0;
    commands.push_back(command);
  }

  Logger::info(kLogTagCmd, "command_count", static_cast<int>(commands.size()));

  return commands;
}
