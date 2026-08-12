#include "http_config_service.h"
#include "config_store.h"

ESP8266WebServer* HttpConfigService::_srv = nullptr;

HttpConfigService& HttpConfigService::instance()
{
    static HttpConfigService ins;
    return ins;
}

void HttpConfigService::begin(ESP8266WebServer &server)
{
    _srv = &server;
    _srv->on("/", handleRoot);
    _srv->on("/config", handleIndex);
    _srv->on("/config/save", HTTP_POST, handleSave);
}

static const char* safeStr(const char* s)
{
    return s ? s : "";
}

void HttpConfigService::handleRoot()
{
    _srv->sendHeader("Location", "/config");
    _srv->send(302, "text/plain", "Redirecting to /config");
}

void HttpConfigService::handleIndex()
{
    auto& cfg = ConfigStore::instance().getConfig();

    String html = String();
    html += "<!DOCTYPE html><html lang=\"zh-CN\"><head>";
    html += "<meta charset=\"UTF-8\">";
    html += "<title>ESP8266设备配置</title></head><body>";
    html += "<h2>设备参数配置</h2>";
    html += "<form method=\"POST\" action=\"/config/save\">";
    html += "ServoPin:<br><input name=\"servoPin\" value=\"" + String(cfg.servoPin) + "\"><br><br>";
    html += "WiFi SSID:<br><input name=\"ssid\" value=\"" + String(safeStr(cfg.wifiSsid)) + "\"><br><br>";
    html += "WiFi Password:<br><input name=\"pwd\" value=\"" + String(safeStr(cfg.wifiPassword)) + "\"><br><br>";
    html += "MQTT Server:<br><input name=\"mqttServer\" value=\"" + String(safeStr(cfg.mqttServer)) + "\"><br><br>";
    html += "MQTT Port:<br><input name=\"mqttPort\" value=\"" + String(cfg.mqttPort) + "\"><br><br>";
    html += "MQTT Topic:<br><input name=\"mqttTopic\" value=\"" + String(safeStr(cfg.mqttTopic)) + "\"><br><br>";
    html += "MQTT ClientId:<br><input name=\"mqttCliId\" value=\"" + String(safeStr(cfg.mqttClientId)) + "\"><br><br>";
    html += "<button type=\"submit\">保存并重启设备</button>";
    html += "</form></body></html>";

    _srv->send(200, "text/html", html);
}

void HttpConfigService::handleSave()
{
    auto& doc = ConfigStore::instance().getJsonDoc();

    doc["servoPin"] = _srv->arg("servoPin").toInt();

    doc["wifiSsid"] = _srv->arg("ssid");
    doc["wifiPassword"] = _srv->arg("pwd");
    doc["mqttServer"] = _srv->arg("mqttServer");
    doc["mqttPort"] = _srv->arg("mqttPort").toInt();
    doc["mqttTopic"] = _srv->arg("mqttTopic");
    doc["mqttClientId"] = _srv->arg("mqttCliId");

    bool ok = ConfigStore::instance().save();
    if (ok)
    {
        _srv->send(200, "text/plain", "配置保存成功，设备即将重启");
        delay(600);
        ESP.restart();
    }
    else
    {
        _srv->send(500, "text/plain", "LittleFS写入失败");
    }
}