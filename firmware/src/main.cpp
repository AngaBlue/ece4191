#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include <WebServer.h>

#ifndef CAM_PIN_XCLK
#error "Camera pins not defined. Ensure scripts/camera_pins.py sets CAM_PIN_* macros."
#endif

// ---- Quick test as AP (no router needed) ----
static const char *AP_SSID = "S3CamTest";
static const char *AP_PASS = "12345678"; // 8+ chars required by ESP AP

WebServer server(80);

// Minimal homepage
static const char INDEX_HTML[] PROGMEM = R"HTML(
<!doctype html><html>
<head><meta name=viewport content="width=device-width,initial-scale=1">
<title>ESP32-S3 Cam</title>
<style>body{font-family:system-ui;margin:20px}img{max-width:100%;height:auto;border:1px solid #ccc}</style>
</head>
<body>
<h3>ESP32-S3 Camera</h3>
<p><a href="/jpg">Take still</a></p>
<img src="/stream">
</body></html>
)HTML";

// Single JPEG endpoint
void handle_jpg()
{
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb)
  {
    server.send(503, "text/plain", "Camera capture failed");
    return;
  }

  // Tell WebServer we're sending a known-length body, then push the body
  server.setContentLength(fb->len);
  server.send(200, "image/jpeg", ""); // sends headers only
  server.sendContent(reinterpret_cast<const char *>(fb->buf), fb->len);
  esp_camera_fb_return(fb);
}

// MJPEG stream endpoint
void handle_stream()
{
  static const char *BOUNDARY = "frame";
  WiFiClient client = server.client();
  String hdr =
      "HTTP/1.1 200 OK\r\n"
      "Content-Type: multipart/x-mixed-replace; boundary=" +
      String(BOUNDARY) + "\r\n"
                         "Pragma: no-cache\r\nCache-Control: no-cache\r\n\r\n";
  client.print(hdr);

  while (client.connected())
  {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb)
      break;

    client.printf("--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", BOUNDARY, fb->len);
    size_t to_write = fb->len;
    const uint8_t *buf = fb->buf;
    while (to_write)
    {
      size_t n = client.write(buf, to_write);
      if (!n)
      {
        esp_camera_fb_return(fb);
        return;
      }
      to_write -= n;
      buf += n;
    }
    client.print("\r\n");
    esp_camera_fb_return(fb);
    // small yield to keep WiFi happy
    delay(5);
  }
}

// Camera init
bool init_camera()
{
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = CAM_PIN_D0;
  c.pin_d1 = CAM_PIN_D1;
  c.pin_d2 = CAM_PIN_D2;
  c.pin_d3 = CAM_PIN_D3;
  c.pin_d4 = CAM_PIN_D4;
  c.pin_d5 = CAM_PIN_D5;
  c.pin_d6 = CAM_PIN_D6;
  c.pin_d7 = CAM_PIN_D7;
  c.pin_xclk = CAM_PIN_XCLK;
  c.pin_pclk = CAM_PIN_PCLK;
  c.pin_vsync = CAM_PIN_VSYNC;
  c.pin_href = CAM_PIN_HREF;
  c.pin_sccb_sda = CAM_PIN_SIOD;
  c.pin_sccb_scl = CAM_PIN_SIOC;
  c.pin_pwdn = CAM_PIN_PWDN;
  c.pin_reset = CAM_PIN_RESET;
  c.xclk_freq_hz = 20000000;
  c.frame_size = FRAMESIZE_UXGA;
  c.jpeg_quality = 8;
  c.fb_count = 4;
  c.fb_location = CAMERA_FB_IN_PSRAM;
  c.grab_mode = CAMERA_GRAB_LATEST;
  c.pixel_format = PIXFORMAT_JPEG;

  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK)
    return false;

  sensor_t *s = esp_camera_sensor_get();
  return true;
}

void setup()
{
  Serial.begin(115200);
  delay(200);
  Serial.println("Booted");
  if (!init_camera())
  {
    Serial.println("Camera init failed");
    for (;;)
      delay(1000);
  }
  Serial.println("Camera init OK");

  // Start AP (fastest path)
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);
  bool ok = WiFi.softAP(AP_SSID, AP_PASS);
  if (!ok)
  {
    Serial.println("AP start failed");
    for (;;)
      delay(1000);
  }
  Serial.print("AP SSID: ");
  Serial.println(AP_SSID);
  Serial.print("AP Pass: ");
  Serial.println(AP_PASS);
  Serial.print("AP IP:   ");
  Serial.println(WiFi.softAPIP());

  server.on("/", []()
            { server.send_P(200, "text/html", INDEX_HTML); });
  server.on("/jpg", handle_jpg);
  server.on("/stream", HTTP_GET, handle_stream);
  server.begin();
  Serial.println("HTTP server started");
}

void loop()
{
  server.handleClient();
}
