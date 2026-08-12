#include "door_command.h"

#include <ArduinoJson.h>

#include "logger.h"

namespace
{
  const char *kLogTagCmd = "CMD";
} // namespace

DoorCommandMessage parseDoorCommandMessage(const byte *payload, unsigned int length)
{
  DoorCommandMessage msg;
  msg.type = MqttCmdType::Unknown;

  String message;
  message.reserve(length);
  for (unsigned int i = 0; i < length; ++i)
  {
    message += static_cast<char>(payload[i]);
  }

  Logger::info(kLogTagCmd, "payload", message);

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, message);
  if (err)
  {
    Logger::error(kLogTagCmd, "deserializeJson() failed");
    return msg;
  }

  const char *type = doc["type"] | "";

  if (strcmp(type, "init") == 0)
  {
    msg.type = MqttCmdType::Init;
    msg.initConfig.pin = doc["pin"] | 5;
    msg.initConfig.minAngle = doc["minAngle"] | 0;
    msg.initConfig.maxAngle = doc["maxAngle"] | 180;
    msg.initConfig.initialAngle = doc["initialAngle"] | 0;

    char logBuf[64];
    snprintf(logBuf, sizeof(logBuf), "init: pin=%d range=%d-%d angle=%d",
             msg.initConfig.pin, msg.initConfig.minAngle,
             msg.initConfig.maxAngle, msg.initConfig.initialAngle);
    Logger::info(kLogTagCmd, logBuf);
  }
  else if (strcmp(type, "rotate") == 0)
  {
    msg.type = MqttCmdType::Rotate;

    JsonArray actions = doc["actions"].as<JsonArray>();
    if (actions.isNull())
    {
      // Legacy: treat the whole doc as an array
      if (doc.is<JsonArray>())
      {
        actions = doc.as<JsonArray>();
      }
    }

    for (JsonObject action : actions)
    {
      DoorCommand cmd;
      cmd.angle = action["angle"] | 0;
      cmd.duration = action["duration"] | action["delay"] | 0;
      msg.commands.push_back(cmd);
    }

    char logBuf[64];
    snprintf(logBuf, sizeof(logBuf), "rotate: %d commands", (int)msg.commands.size());
    Logger::info(kLogTagCmd, logBuf);
  }
  else
  {
    // Legacy: treat as array of commands
    if (doc.is<JsonArray>())
    {
      msg.type = MqttCmdType::Rotate;
      JsonArray arr = doc.as<JsonArray>();
      for (JsonObject obj : arr)
      {
        DoorCommand cmd;
        cmd.angle = obj["angle"] | 0;
        cmd.duration = obj["duration"] | obj["delay"] | 0;
        msg.commands.push_back(cmd);
      }
      Logger::info(kLogTagCmd, "legacy array format", String((int)msg.commands.size()) + " commands");
    }
    else
    {
      Logger::warn(kLogTagCmd, "Unknown command type");
    }
  }

  return msg;
}

std::vector<DoorCommand> parseDoorCommands(const byte *payload, unsigned int length)
{
  String message;
  message.reserve(length);
  for (unsigned int i = 0; i < length; ++i)
  {
    message += static_cast<char>(payload[i]);
  }

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, message);
  if (err)
  {
    Logger::error(kLogTagCmd, "deserializeJson() failed");
    return {};
  }

  std::vector<DoorCommand> commands;
  JsonArray jsonArray = doc.as<JsonArray>();

  for (JsonObject object : jsonArray)
  {
    DoorCommand command{};
    command.angle = object["angle"] | 0;
    command.duration = object["duration"] | 0;
    commands.push_back(command);
  }

  return commands;
}
