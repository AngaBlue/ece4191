#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32-RTSPServer.h>
#include "esp_camera.h"
#include "pins.h"
#include "config.h"
#include "motor_control.h"
#include "pwm_led.h"

RTSPServer rtspServer;
WiFiUDP udp;
char packetBuffer[255];

// RTSP
int quality;
TaskHandle_t videoTaskHandle = NULL;

MotorControl motorControl;
PwmLed irLed(PIN_IR_LED);

#ifdef audio_enabled
#include <ESP_I2S.h>
I2SClass I2S;
int sampleRate = 48000;
const size_t sampleBytes = 1024;
int16_t *sampleBuffer = NULL;
TaskHandle_t audioTaskHandle = NULL;
#endif

static bool networkReady = false;
static unsigned long lastWifiAttempt = 0;
static unsigned long lastMovementCommand = 0;

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

enum Command : uint8_t
{
  CMD_BRIGHTNESS = 0x01,
  CMD_MOVEMENT = 0x02,
  CMD_CAMERA = 0x03,
};

static uint8_t checksum(const uint8_t *buf, size_t n)
{
  uint16_t s = 0;
  for (size_t i = 0; i < n; ++i)
    s += buf[i];
  return s & 0xFF;
}

static bool readExactly(uint8_t *dst, size_t n)
{
  size_t read = 0;
  while (read < n)
  {
    int c = udp.read(dst + read, n - read);
    if (c <= 0)
      return false;
    read += (size_t)c;
  }
  return true;
}

void onCamera(float x, float y)
{
  Serial.printf("Camera: %.4f, %.4f\n", x, y);
}

#ifdef audio_enabled
static void init_mic()
{
  // I2S mic and I2S amp can share same I2S channel
  I2S.setPins(PIN_I2S_SCK, PIN_I2S_WS, -1, PIN_I2S_SD, -1); // BCLK/SCK, LRCLK/WS, SDOUT, SDIN, MCLK
  bool res = I2S.begin(I2S_MODE_STD, sampleRate, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);
  if (sampleBuffer == NULL)
    sampleBuffer = (int16_t *)malloc(sampleBytes);

  if (!res)
  {
    Serial.println("Microphone: init failed");
    hang();
  }
  Serial.println("Microphone: init successful");
}

static size_t micInput()
{
  size_t bytesRead = 0;
  bytesRead = I2S.readBytes((char *)sampleBuffer, sampleBytes);
  return bytesRead;
}

void sendAudio(void *pvParameters)
{
  while (true)
  {
    if (rtspServer.readyToSendAudio())
    {
      size_t bytesRead = micInput();
      if (bytesRead)
        rtspServer.sendRTSPAudio(sampleBuffer, bytesRead);
      else
        Serial.println("No audio received");
    }
    vTaskDelay(pdMS_TO_TICKS(1));
  }
}
#endif

// ===== Movement handler =====
void onMovement(float translation, float rotation)
{
  float left = constrain(translation - rotation, -1.0f, 1.0f);
  float right = constrain(translation + rotation, -1.0f, 1.0f);
  motorControl.setVelocityOpenLoop(left, right);
  Serial.printf("[UDP] Movement command: T=%.2f R=%.2f -> L=%.2f R=%.2f\n",
                translation, rotation, left, right);
}

void onBrightness(int16_t level)
{
  Serial.printf("Brightness Level: %d\n", (int)level);
  irLed.onBrightness(level);
}

// ====== Wi-Fi (STA) helpers ======
static void printIPAndStartNetServicesIfNeeded()
{
  if (WiFi.status() != WL_CONNECTED)
    return;

  IPAddress ip = WiFi.localIP();
  if (!networkReady)
  {
    // Start UDP + RTSP only once we have a valid IP
    udp.begin(UDP_PORT);

    getFrameQuality();
#ifdef audio_enabled
    rtspServer.transport = RTSPServer::VIDEO_AND_AUDIO;
#else
    rtspServer.transport = RTSPServer::VIDEO_ONLY;
#endif

    if (rtspServer.init())
    {
      Serial.printf("RTSP server started. Connect to rtsp://%s:554/\n", ip.toString().c_str());
    }
    else
    {
      Serial.println("Failed to start RTSP server");
    }
    networkReady = true;
  }

  static bool printed = false;
  if (!printed)
  {
    Serial.print("Wi-Fi connected. IP: ");
    Serial.println(ip);
    printed = true;
  }
}

static void maintainWiFi()
{
  // Already connected
  if (WiFi.status() == WL_CONNECTED)
  {
    printIPAndStartNetServicesIfNeeded();
    return;
  }

  // Not connected — allow services to remain; they will resume once IP is back.
  networkReady = false; // forces services to re-announce next time we connect

  unsigned long now = millis();
  if (now - lastWifiAttempt >= WIFI_RETRY_MS)
  {
    Serial.printf("Wi-Fi: attempting to connect to \"%s\"...\n", HOTSPOT_SSID);
    WiFi.disconnect(true, true);
    delay(100);
    WiFi.begin(HOTSPOT_SSID, HOTSPOT_PASS);
    lastWifiAttempt = now;
  }
}

static void parseControlInputs()
{
  // If not connected yet, just return; control packets require network
  if (WiFi.status() != WL_CONNECTED)
  {
    delay(10);
    return;
  }

  // ==== UDP control protocol ====
  int pktLen = udp.parsePacket();
  if (pktLen <= 0)
    return;

  uint8_t hdr[3];
  if (!readExactly(hdr, sizeof(hdr)))
  {
    while (udp.available())
      udp.read();
    return;
  }
  uint8_t cmd = hdr[0], len = hdr[1], id = hdr[2];

  if (udp.available() < (int)len + 1)
  {
    while (udp.available())
      udp.read();
    return;
  }
  uint8_t payload[16];
  if (len > sizeof(payload))
  {
    while (udp.available())
      udp.read();
    return;
  }
  if (!readExactly(payload, len))
  {
    while (udp.available())
      udp.read();
    return;
  }
  uint8_t chk = 0;
  if (!readExactly(&chk, 1))
  {
    while (udp.available())
      udp.read();
    return;
  }

  uint8_t tmp[3 + 16];
  memcpy(tmp, hdr, 3);
  memcpy(tmp + 3, payload, len);
  uint8_t calc = checksum(tmp, 3 + len);
  if (chk != calc)
    return;

  switch (cmd)
  {
  case CMD_BRIGHTNESS:
    if (len == 2)
    {
      int16_t level;
      memcpy(&level, payload, 2);
      onBrightness(level);
    }
    break;

  case CMD_MOVEMENT:
    if (len == 8)
    {
      float x, y;
      memcpy(&x, payload + 0, 4);
      memcpy(&y, payload + 4, 4);
      lastMovementCommand = millis();
      onMovement(x, y);
    }
    break;

  case CMD_CAMERA:
    if (len == 8)
    {
      float x, y;
      memcpy(&x, payload + 0, 4);
      memcpy(&y, payload + 4, 4);
      onCamera(x, y);
    }
    break;

  default:
    break;
  }
}

void setup()
{
  Serial.begin(115200);
  Serial.println("Booted!");

  init_camera();
  irLed.begin();
  motorControl.begin();

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setHostname(NAME);

  // Start video task immediately; it will send frames when RTSP is ready
  xTaskCreatePinnedToCore(sendVideo, "Video", 12288, NULL, 9, &videoTaskHandle, APP_CPU_NUM);

#ifdef audio_enabled
  init_mic();
  xTaskCreate(sendAudio, "Audio", 8192, NULL, 8, &audioTaskHandle);
#endif

  // Kick off the first connection attempt right away
  lastWifiAttempt = millis() - WIFI_RETRY_MS;
  maintainWiFi();
}

void loop()
{
  // Keep trying to connect (or reconnect) in the background
  maintainWiFi();

  // Receive and action incoming packets
  parseControlInputs();

  // Stop movement after no inputs are received
  unsigned long now = millis();
  if (now - lastMovementCommand > MOVEMENT_TIMEOUT)
  {
    motorControl.setVelocityOpenLoop(0.0f, 0.0f);
  }
}
