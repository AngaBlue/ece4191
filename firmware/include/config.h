#include "esp_camera.h"
#include <WiFi.h>

/**
 * WiFi
 */
static const char *NAME = "ESP32S3-R06";
static const char *HOTSPOT_SSID = "ANGUS-DESKTOP";
static const char *HOTSPOT_PASS = "12345678";
static const unsigned long WIFI_RETRY_MS = 5000;

/**
 * Camera
 */
#define FRAME_SIZE FRAMESIZE_VGA
#define JPEG_QUALITY 10
#define FRAME_BUFFER_COUNT 1

/**
 * RTSP
 */
#define RTSP_VIDEO_NONBLOCK

/**
 * UDP
 */
#define UDP_PORT 65001

/**
 * Motors
 */
#define MOVEMENT_TIMEOUT 200

/**
 * Servos
 */
static constexpr int SERVO_MIN_US = 500;
static constexpr int SERVO_MAX_US = 2500;
static constexpr int SERVO_FREQ_HZ = 50;
static constexpr int SERVO_RANGE_DEG = 270;
