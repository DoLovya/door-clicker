#include "logger.h"

namespace Logger
{
namespace
{
const char *levelToString(Level level)
{
  switch (level)
  {
  case Level::Info:
    return "INFO";
  case Level::Warn:
    return "WARN";
  case Level::Error:
    return "ERROR";
  }

  return "INFO";
}
} // namespace

void begin(long baudRate)
{
  Serial.begin(baudRate);
}

void log(Level level, const char *tag, const String &message)
{
  Serial.printf(
      "[%08lu][%s][%s] %s\n", millis(), levelToString(level), tag, message.c_str());
}

void info(const char *tag, const String &message)
{
  log(Level::Info, tag, message);
}

void info(const char *tag, const char *message)
{
  log(Level::Info, tag, String(message));
}

void info(const char *tag, const char *key, const String &value)
{
  log(Level::Info, tag, String(key) + "=" + value);
}

void info(const char *tag, const char *key, int value)
{
  log(Level::Info, tag, String(key) + "=" + String(value));
}

void warn(const char *tag, const String &message)
{
  log(Level::Warn, tag, message);
}

void warn(const char *tag, const char *message)
{
  log(Level::Warn, tag, String(message));
}

void warn(const char *tag, const char *key, const String &value)
{
  log(Level::Warn, tag, String(key) + "=" + value);
}

void warn(const char *tag, const char *key, int value)
{
  log(Level::Warn, tag, String(key) + "=" + String(value));
}

void error(const char *tag, const String &message)
{
  log(Level::Error, tag, message);
}

void error(const char *tag, const char *message)
{
  log(Level::Error, tag, String(message));
}

void error(const char *tag, const char *key, const String &value)
{
  log(Level::Error, tag, String(key) + "=" + value);
}

void error(const char *tag, const char *key, int value)
{
  log(Level::Error, tag, String(key) + "=" + String(value));
}
} // namespace Logger
