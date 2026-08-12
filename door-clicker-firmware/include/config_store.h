#pragma once
#include <ArduinoJson.h>
#include <LittleFS.h>

struct AppConfigData
{
    int servoPin;

    const char* wifiSsid;
    const char* wifiPassword;

    const char* mqttServer;
    int mqttPort;
    const char* mqttTopic;
    const char* mqttClientId;
};

class ConfigStore
{
public:
    static ConfigStore& instance();

    // 返回true：加载成功；false：文件不存在/解析失败，结构体无效
    bool load();
    bool save();

    const AppConfigData& getConfig() const;
    DynamicJsonDocument& getJsonDoc();

private:
    ConfigStore();
    AppConfigData _cfg;
    DynamicJsonDocument _doc;

    // 将 _doc 同步到 _cfg 结构体
    void syncDocToStruct();
};