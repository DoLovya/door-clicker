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

    _srv->sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
    _srv->sendHeader("Pragma", "no-cache");
    _srv->sendHeader("Expires", "0");

    // Use chunked transfer to avoid large String allocation
    _srv->setContentLength(CONTENT_LENGTH_UNKNOWN);
    _srv->send(200, "text/html; charset=utf-8", "");

    _srv->sendContent(R"HTML(
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Door Clicker 配置</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;min-height:100vh;padding:20px}
.container{max-width:480px;margin:0 auto}
.header{text-align:center;padding:24px 0 20px}
.header h1{font-size:22px;color:#1a1a2e;font-weight:600}
.header p{font-size:13px;color:#888;margin-top:6px}
.card{background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
.card-title{font-size:13px;font-weight:600;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #eee}
.field{margin-bottom:14px}
.field label{display:block;font-size:13px;color:#555;margin-bottom:5px;font-weight:500}
.field input{width:100%;padding:9px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;background:#fafafa;transition:border .2s}
.field input:focus{outline:none;border-color:#4a90d9;background:#fff}
.pwd-wrap{position:relative}
.pwd-wrap input{padding-right:42px}
.pwd-eye{position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;padding:6px;color:#888;font-size:16px;line-height:1;user-select:none;display:none}
.pwd-wrap:focus-within .pwd-eye{display:block}
.pwd-eye:hover{color:#333}
.field-row{display:flex;gap:12px}
.field-row .field{flex:1}
.btn{display:block;width:100%;padding:12px;background:#1a1a2e;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;transition:background .2s}
.btn:hover{background:#2d2d44}
.btn:active{background:#0f0f1f}
.footer{text-align:center;padding:16px;font-size:11px;color:#aaa}
.dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#4caf50;margin-right:6px;vertical-align:middle}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1><span class="dot"></span>Door Clicker</h1>
<p>设备参数配置</p>
</div>
<form method="POST" action="/config/save">
<div class="card">
<div class="card-title">设备</div>
<div class="field">
<label>舵机引脚</label>
)HTML");

    _srv->sendContent("<input name=\"servoPin\" value=\"" + String(cfg.servoPin) + "\" placeholder=\"5\">");
    _srv->sendContent(R"HTML(
</div>
</div>
<div class="card">
<div class="card-title">Wi-Fi</div>
<div class="field">
<label>SSID</label>
)HTML");
    _srv->sendContent("<input name=\"ssid\" value=\"" + String(safeStr(cfg.wifiSsid)) + "\" placeholder=\"MyWiFi\">");
    _srv->sendContent(R"HTML(
</div>
<div class="field">
<label>密码</label>
<div class="pwd-wrap">
)HTML");
    _srv->sendContent("<input name=\"pwd\" id=\"pwd\" type=\"password\" value=\"" + String(safeStr(cfg.wifiPassword)) + "\" placeholder=\"Password\">");
    _srv->sendContent(R"HTML(
<button type="button" class="pwd-eye" onclick="togglePwd()" title="显示/隐藏">👁</button>
</div>
</div>
</div>
<div class="card">
<div class="card-title">MQTT</div>
<div class="field">
<label>服务器地址</label>
)HTML");
    _srv->sendContent("<input name=\"mqttServer\" value=\"" + String(safeStr(cfg.mqttServer)) + "\" placeholder=\"192.168.1.1\">");
    _srv->sendContent(R"HTML(
</div>
<div class="field-row">
<div class="field">
<label>端口</label>
)HTML");
    _srv->sendContent("<input name=\"mqttPort\" value=\"" + String(cfg.mqttPort) + "\" placeholder=\"1883\">");
    _srv->sendContent(R"HTML(
</div>
</div>
</div>
<button type="submit" class="btn">保存并重启设备</button>
</form>
<div class="footer">v1.0 · Door Clicker</div>
</div>
<script>function togglePwd(){var i=document.getElementById('pwd');i.type=i.type==='password'?'text':'password'}</script>
</body>
</html>
)HTML");

    _srv->sendContent("");
}

void HttpConfigService::handleSave()
{
    auto& doc = ConfigStore::instance().getJsonDoc();

    doc["servoPin"] = _srv->arg("servoPin").toInt();
    doc["wifiSsid"] = _srv->arg("ssid");
    doc["wifiPassword"] = _srv->arg("pwd");
    doc["mqttServer"] = _srv->arg("mqttServer");
    doc["mqttPort"] = _srv->arg("mqttPort").toInt();

    bool ok = ConfigStore::instance().save();
    if (ok)
    {
        _srv->send(200, "text/html",
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            "<meta http-equiv='refresh' content='2;url=/config'>"
            "<style>body{font-family:sans-serif;display:flex;align-items:center;"
            "justify-content:center;height:100vh;margin:0;background:#f0f2f5}"
            ".box{text-align:center;background:#fff;padding:30px 40px;border-radius:12px;"
            "box-shadow:0 1px 3px rgba(0,0,0,.08)}h2{color:#4caf50;margin:0 0 8px}"
            "p{color:#888;margin:0}</style></head><body><div class='box'>"
            "<h2>✓ 保存成功</h2><p>设备即将重启...</p></div></body></html>");
        delay(800);
        ESP.restart();
    }
    else
    {
        _srv->send(500, "text/html",
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            "<style>body{font-family:sans-serif;display:flex;align-items:center;"
            "justify-content:center;height:100vh;margin:0;background:#f0f2f5}"
            ".box{text-align:center;background:#fff;padding:30px 40px;border-radius:12px;"
            "box-shadow:0 1px 3px rgba(0,0,0,.08)}h2{color:#e53935;margin:0 0 8px}"
            "p{color:#888;margin:0}</style></head><body><div class='box'>"
            "<h2>✗ 保存失败</h2><p>LittleFS写入错误</p></div></body></html>");
    }
}