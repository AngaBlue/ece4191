#include <Arduino.h>
#include <WiFi.h>
#include <ESP32-RTSPServer.h>
#include "esp_camera.h"
#include <WebServer.h>
#include "pins.h"
#include "config.h"

WebServer server(80);
RTSPServer rtspServer;

// RTSP
int quality;
TaskHandle_t videoTaskHandle = NULL;

// Audio
#ifdef audio_enabled
#include <ESP_I2S.h>
// I2SClass object for I2S communication
I2SClass I2S;

// Audio variables
int sampleRate = 48000;          // Sample rate in Hz
const size_t sampleBytes = 1024; // Sample buffer size (in bytes)
int16_t *sampleBuffer = NULL;    // Pointer to the sample buffer
#endif

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

void getFrameQuality()
{
  sensor_t *s = esp_camera_sensor_get();
  quality = s->status.quality;
  Serial.printf("Camera Quality is: %d\n", quality);
}

void sendVideo(void *pvParameters)
{
  while (true)
  {
    if (rtspServer.readyToSendFrame())
    {
      camera_fb_t *fb = esp_camera_fb_get();
      if (fb)
      {
        rtspServer.sendRTSPFrame(fb->buf, fb->len, quality, fb->width, fb->height);
        esp_camera_fb_return(fb);
      }
    }

    vTaskDelay(1);
  }
}

#ifdef audio_enabled
static bool setupMic()
{
  bool res;
  // I2S mic and I2S amp can share same I2S channel
  I2S.setPins(PIN_I2S_SCK, PIN_I2S_WS, -1, PIN_I2S_SD, -1); // BCLK/SCK, LRCLK/WS, SDOUT, SDIN, MCLK
  res = I2S.begin(I2S_MODE_STD, sampleRate, I2S_DATA_BIT_WIDTH_24BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);
  if (sampleBuffer == NULL)
    sampleBuffer = (int16_t *)malloc(sampleBytes);
  return res;
}

/**
 * @brief Reads audio data from the I2S microphone.
 *
 * @return The number of bytes read.
 */
static size_t micInput()
{
  // read esp mic
  size_t bytesRead = 0;
  bytesRead = I2S.readBytes((char *)sampleBuffer, sampleBytes);
  return bytesRead;
}
/**
 * @brief Task to send audio data via RTP.
 */
void sendAudio(void *pvParameters)
{
  while (true)
  {
    size_t bytesRead = 0;
    if (rtspServer.readyToSendAudio())
    {
      bytesRead = micInput();
      if (bytesRead)
        rtspServer.sendRTSPAudio(sampleBuffer, bytesRead);
      else
        Serial.println("No audio Recieved");
    }
    vTaskDelay(pdMS_TO_TICKS(1)); // Delay for 1 second
  }
}
#endif

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

  getFrameQuality();
  rtspServer.maxRTSPClients = 1;
  rtspServer.transport = RTSPServer::VIDEO_ONLY;
  xTaskCreatePinnedToCore(sendVideo, "Video", 12288, NULL, 9, &videoTaskHandle, APP_CPU_NUM);

  if (rtspServer.init())
  {
    Serial.printf("RTSP server started successfully using default values, Connect to rtsp://%s:554/\n", WiFi.softAPIP().toString().c_str());
  }
  else
  {
    Serial.println("Failed to start RTSP server");
  }
}

void loop()
{
  server.handleClient();
}
