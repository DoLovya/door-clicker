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

    // mqttUsername
    s = _doc["mqttUsername"] | "";
    _cfg.mqttUsername = s;
    Logger::info("CFG", "mqttUsername", String(s ? s : "(null)"));

    // mqttPassword
    s = _doc["mqttPassword"] | "";
    _cfg.mqttPassword = s;
    Logger::info("CFG", "mqttPassword length", String(s ? strlen(s) : 0));

    // servoPin (D4 = GPIO2)
    _cfg.servoPin = _doc["servoPin"] | 2;
    Logger::info("CFG", "servoPin", _cfg.servoPin);

    // servoMinAngle
    _cfg.servoMinAngle = _doc["servoMinAngle"] | 0;
    Logger::info("CFG", "servoMinAngle", _cfg.servoMinAngle);

    // servoMaxAngle
    _cfg.servoMaxAngle = _doc["servoMaxAngle"] | 180;
    Logger::info("CFG", "servoMaxAngle", _cfg.servoMaxAngle);

    // servoInitialAngle
    _cfg.servoInitialAngle = _doc["servoInitialAngle"] | 0;
    Logger::info("CFG", "servoInitialAngle", _cfg.servoInitialAngle);
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