#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include "door_clicker_app.h"
#include "config_store.h"
#include "http_config_service.h"
#include "logger.h"

namespace
{
  constexpr long kSerialBaudRate = 19200;
  constexpr const char *kApSsid = "DoorClicker";
  constexpr const char *kApPassword = "door1234";
}

DoorClickerApp app;
ESP8266WebServer server(80);
bool configValid = false;

void setup()
{
  Serial.begin(kSerialBaudRate);
  delay(100);

  Logger::info("BOOT", "Serial started");

  configValid = ConfigStore::instance().load();

  if (configValid)
  {
    Logger::info("BOOT", "Config loaded successfully");
  }
  else
  {
    Logger::warn("BOOT", "No valid config.json, visit /config to set up");
  }

  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(kApSsid, kApPassword);
  Logger::info("BOOT", "AP started");
  Logger::info("BOOT", "ssid", String(kApSsid));
  Logger::info("BOOT", "password", String(kApPassword));
  Logger::info("BOOT", "ap_ip", WiFi.softAPIP().toString());

  app.setup();

  HttpConfigService::instance().begin(server);
  server.begin();
  Logger::info("BOOT", "HTTP server started on port 80");
}

void loop()
{
  app.loop();
  server.handleClient();
}