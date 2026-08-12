#pragma once
#include <ESP8266WebServer.h>

class HttpConfigService
{
public:
    static HttpConfigService& instance();
    void begin(ESP8266WebServer &server);

private:
    HttpConfigService() = default;
    static void handleRoot();
    static void handleIndex();
    static void handleSave();
    static ESP8266WebServer* _srv;
};