#include "esp_camera.h"

/**
 * Miscellaneous
 */
static const char *NAME = "ESP32S3-R06";
static const char *AP_SSID = NAME;
static const char *AP_PASS = "12345678";

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
