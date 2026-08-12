#pragma once

#include <Arduino.h>

namespace Logger
{
  enum class Level
  {
    Info,
    Warn,
    Error,
  };

  void log(Level level, const char *tag, const String &message);
  void info(const char *tag, const String &message);
  void info(const char *tag, const char *message);
  void info(const char *tag, const char *key, const String &value);
  void info(const char *tag, const char *key, const char *value);
  void info(const char *tag, const char *key, int value);

  void warn(const char *tag, const String &message);
  void warn(const char *tag, const char *message);
  void warn(const char *tag, const char *key, const String &value);
  void warn(const char *tag, const char *key, const char *value);
  void warn(const char *tag, const char *key, int value);

  void error(const char *tag, const String &message);
  void error(const char *tag, const char *message);
  void error(const char *tag, const char *key, const String &value);
  void error(const char *tag, const char *key, const char *value);
  void error(const char *tag, const char *key, int value);
} // namespace Logger