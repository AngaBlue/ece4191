#include "esp_camera.h"
#include <WiFi.h>

/**
 * WiFi
 */
static const char *NAME = "ESP32S3-R06";
static const char *HOTSPOT_SSID = "ESP32S3-R06";
static const char *HOTSPOT_PASS = "Sb5bo$A33D4K3QK3";
static const unsigned long WIFI_RETRY_MS = 5000;

/**
 * Camera
 */
#define FRAME_SIZE FRAMESIZE_VGA
#define JPEG_QUALITY 5
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
static constexpr int SERVO_PAN_MIN_DEG = 0;
static constexpr int SERVO_PAN_MAX_DEG = 270;
static constexpr int SERVO_TILT_MIN_DEG = 100;
static constexpr int SERVO_TILT_MAX_DEG = 270;
