#include "config_store.h"

ConfigStore& ConfigStore::instance()
{
    static ConfigStore ins;
    return ins;
}

ConfigStore::ConfigStore() : _doc(1024)
{
    memset(&_cfg, 0, sizeof(_cfg));
}

DynamicJsonDocument& ConfigStore::getJsonDoc()
{
    return _doc;
}

void ConfigStore::syncDocToStruct()
{
    _cfg.servoPin = _doc["servoPin"] | 0;

    _cfg.wifiSsid = _doc["wifiSsid"].as<const char*>();
    if (!_cfg.wifiSsid) _cfg.wifiSsid = "";
    _cfg.wifiPassword = _doc["wifiPassword"].as<const char*>();
    if (!_cfg.wifiPassword) _cfg.wifiPassword = "";
    _cfg.mqttServer = _doc["mqttServer"].as<const char*>();
    if (!_cfg.mqttServer) _cfg.mqttServer = "";
    _cfg.mqttPort = _doc["mqttPort"] | 0;
    _cfg.mqttTopic = _doc["mqttTopic"].as<const char*>();
    if (!_cfg.mqttTopic) _cfg.mqttTopic = "";
    _cfg.mqttClientId = _doc["mqttClientId"].as<const char*>();
    if (!_cfg.mqttClientId) _cfg.mqttClientId = "";
}

bool ConfigStore::load()
{
    if (!LittleFS.begin())
    {
        return false;
    }
    File f = LittleFS.open("/config.json", "r");
    if (!f)
    {
        return false;
    }
    auto err = deserializeJson(_doc, f);
    f.close();
    if (err)
    {
        return false;
    }
    syncDocToStruct();
    return true;
}

bool ConfigStore::save()
{
    File f = LittleFS.open("/config.json", "w");
    if (!f) return false;
    serializeJson(_doc, f);
    f.close();
    syncDocToStruct();
    return true;
}

const AppConfigData& ConfigStore::getConfig() const
{
    return _cfg;
}