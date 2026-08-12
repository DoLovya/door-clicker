#include "config_store.h"
#include "logger.h"

ConfigStore& ConfigStore::instance()
{
    static ConfigStore ins;
    return ins;
}

ConfigStore::ConfigStore()
{
    memset(&_cfg, 0, sizeof(_cfg));
}

JsonDocument& ConfigStore::getJsonDoc()
{
    return _doc;
}

void ConfigStore::syncDocToStruct()
{
    Logger::info("CFG", "doc size", _doc.size());

    // servoPin
    _cfg.servoPin = _doc["servoPin"] | 0;
    Logger::info("CFG", "servoPin", _cfg.servoPin);

    // wifiSsid
    const char* s = _doc["wifiSsid"] | "";
    _cfg.wifiSsid = s;
    Logger::info("CFG", "wifiSsid", String(s ? s : "(null)"));

    // wifiPassword
    s = _doc["wifiPassword"] | "";
    _cfg.wifiPassword = s;
    Logger::info("CFG", "wifiPassword length", String(s ? strlen(s) : 0));

    // mqttServer
    s = _doc["mqttServer"] | "";
    _cfg.mqttServer = s;
    Logger::info("CFG", "mqttServer", String(s ? s : "(null)"));

    // mqttPort
    _cfg.mqttPort = _doc["mqttPort"] | 0;
    Logger::info("CFG", "mqttPort", _cfg.mqttPort);
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