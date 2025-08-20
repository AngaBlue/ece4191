#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include <WebServer.h>
#include "pins.h"
#include "config.h"

WebServer server(80);

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

void hang()
{
  while (true)
    delay(1000);
}

void init_camera()
{
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = PIN_CAM_D0;
  c.pin_d1 = PIN_CAM_D1;
  c.pin_d2 = PIN_CAM_D2;
  c.pin_d3 = PIN_CAM_D3;
  c.pin_d4 = PIN_CAM_D4;
  c.pin_d5 = PIN_CAM_D5;
  c.pin_d6 = PIN_CAM_D6;
  c.pin_d7 = PIN_CAM_D7;
  c.pin_xclk = PIN_CAM_XCLK;
  c.pin_pclk = PIN_CAM_PCLK;
  c.pin_vsync = PIN_CAM_VSYNC;
  c.pin_href = PIN_CAM_HREF;
  c.pin_sccb_sda = PIN_CAM_SIOD;
  c.pin_sccb_scl = PIN_CAM_SIOC;
  c.pin_pwdn = PIN_CAM_PWDN;
  c.pin_reset = PIN_CAM_RESET;
  c.xclk_freq_hz = 20000000;
  c.frame_size = FRAME_SIZE;
  c.jpeg_quality = JPEG_QUALITY;
  c.fb_count = FRAME_BUFFER_COUNT;
  c.fb_location = CAMERA_FB_IN_PSRAM;
  c.grab_mode = CAMERA_GRAB_LATEST;
  c.pixel_format = PIXFORMAT_JPEG;

  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK)
  {
    Serial.println("Camera: init failed");
    hang();
  }

  sensor_t *s = esp_camera_sensor_get();
  Serial.println("Camera: init successful");
}

void init_ap()
{
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);
  bool ok = WiFi.softAP(AP_SSID, AP_PASS, 1, 0, 1);
  if (!ok)
  {
    Serial.println("AP: init failed");
    hang();
  }
  Serial.print("AP SSID: ");
  Serial.println(AP_SSID);
  Serial.print("AP Pass: ");
  Serial.println(AP_PASS);
  Serial.print("AP IP:   ");
  Serial.println(WiFi.softAPIP());
}

void setup()
{
  Serial.begin(115200);
  Serial.println("Booted!");

  init_camera();
  init_ap();

  server.on("/jpg", handle_jpg);
  server.on("/stream", HTTP_GET, handle_stream);
  server.begin();
  Serial.println("HTTP server started");
}

void loop()
{
  server.handleClient();
}
