#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32-RTSPServer.h>
#include "esp_camera.h"
#include "pins.h"
#include "config.h"

RTSPServer rtspServer;
WiFiUDP udp;
char packetBuffer[255];

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
TaskHandle_t audioTaskHandle = NULL;
#endif

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
static void init_mic()
{
  bool res;
  // I2S mic and I2S amp can share same I2S channel
  I2S.setPins(PIN_I2S_SCK, PIN_I2S_WS, -1, PIN_I2S_SD, -1); // BCLK/SCK, LRCLK/WS, SDOUT, SDIN, MCLK
  res = I2S.begin(I2S_MODE_STD, sampleRate, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);
  if (sampleBuffer == NULL)
    sampleBuffer = (int16_t *)malloc(sampleBytes);

  if (res != true)
  {
    Serial.println("Microphone: init failed");
    hang();
  }

  Serial.println("Microphone: init successful");
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

void onBrightness(int16_t level)
{
  Serial.printf("Brightness Level %u", level);
}
void onMovement(float x, float y)
{
  // e.g., robot/gamepad movement
}
void onCamera(float x, float y)
{
  // e.g., gimbal/camera pan-tilt
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
#ifdef audio_enabled
  init_mic();
#endif

  udp.begin(UDP_PORT);
  Serial.printf("UDP control on %s:%u\n", WiFi.softAPIP().toString().c_str(), UDP_PORT);

  getFrameQuality();
  rtspServer.maxRTSPClients = 1;

#ifdef audio_enabled
  rtspServer.transport = RTSPServer::VIDEO_AND_AUDIO;
  xTaskCreate(sendAudio, "Audio", 8192, NULL, 8, &audioTaskHandle);
#else
  rtspServer.transport = RTSPServer::VIDEO_ONLY;
#endif
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
  int pktLen = udp.parsePacket();
  if (pktLen <= 0)
    return;

  // Minimal header: CMD, LEN, ID
  uint8_t hdr[3];
  if (!readExactly(hdr, sizeof(hdr)))
  {
    while (udp.available())
      udp.read();
    return;
  }
  uint8_t cmd = hdr[0], len = hdr[1], id = hdr[2];

  // Read payload + checksum
  if (udp.available() < (int)len + 1)
  {
    while (udp.available())
      udp.read();
    return;
  }
  uint8_t payload[16]; // enough for our current commands
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

  // Verify checksum
  uint8_t calc = 0;
  {
    uint8_t tmp[3 + 16];
    memcpy(tmp, hdr, 3);
    memcpy(tmp + 3, payload, len);
    calc = checksum(tmp, 3 + len);
  }
  if (chk != calc)
    return; // drop silently or log

  // Dispatch
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
    // Unknown command: ignore (future-proofing)
    break;
  }

  // Optional ACK (uncomment if you want reliability on certain commands)
  // udp.beginPacket(udp.remoteIP(), udp.remotePort());
  // uint8_t ack[2] = { id, 0xAA }; // echo ID + OK marker
  // udp.write(ack, 2);
  // udp.endPacket();
}
