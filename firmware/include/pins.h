/**
 * Camera
 */
#ifdef esp32s3cam_lonelybinary
#define PIN_CAM_PWDN -1 // not connected
#define PIN_CAM_RESET -1 // not connected

#define PIN_CAM_SIOD 4
#define PIN_CAM_SIOC 5

#define PIN_CAM_VSYNC 6
#define PIN_CAM_HREF 7
#define PIN_CAM_XCLK 15
#define PIN_CAM_PCLK 13

#define PIN_CAM_D7 16 // CAM_Y9
#define PIN_CAM_D6 17 // CAM_Y8
#define PIN_CAM_D5 18 // CAM_Y7
#define PIN_CAM_D4 12 // CAM_Y6
#define PIN_CAM_D3 10 // CAM_Y5
#define PIN_CAM_D2 8  // CAM_Y4
#define PIN_CAM_D1 9  // CAM_Y3
#define PIN_CAM_D0 11 // CAM_Y2
#endif

#ifdef esp32cam_aithinker
#define PIN_CAM_PWDN 32
#define PIN_CAM_RESET -1 // not connected

#define PIN_CAM_SIOD 26
#define PIN_CAM_SIOC 27

#define PIN_CAM_VSYNC 25
#define PIN_CAM_HREF 23
#define PIN_CAM_XCLK 0
#define PIN_CAM_PCLK 22

#define PIN_CAM_D7 35 // CAM_Y9
#define PIN_CAM_D6 34 // CAM_Y8
#define PIN_CAM_D5 39 // CAM_Y7
#define PIN_CAM_D4 36 // CAM_Y6
#define PIN_CAM_D3 21 // CAM_Y5
#define PIN_CAM_D2 19 // CAM_Y4
#define PIN_CAM_D1 18 // CAM_Y3
#define PIN_CAM_D0 5  // CAM_Y2

#define PIN_CAM_FLASH 4 // Onboard flash on the ESP32CAM
#endif

/**
 * I2S (Microphone)
 */
#ifdef esp32s3cam_lonelybinary
#define PIN_I2S_SD 1
#define PIN_I2S_WS 2
#define PIN_I2S_SCK 42
#define PIN_I2S_MCK 41
#endif

#ifdef esp32cam_aithinker
#define PIN_I2S_SD  13 // D13 / IO13
#define PIN_I2S_WS  14 // D14 / IO14
#define PIN_I2S_SCK 16 // RX2 / IO16
#endif

/**
 * Servos
 */
#ifdef esp32s3cam_lonelybinary
#define PIN_SERVO_PAN 3
#define PIN_SERVO_TILT 46
#endif

/**
 * Motors
 */
#ifdef esp32s3cam_lonelybinary
#define PIN_M1_IN1 45
#define PIN_M1_IN2 48
#define PIN_M1_ENCA 19
#define PIN_M1_ENCB 47

#define PIN_M2_IN1 39
#define PIN_M2_IN2 40
#define PIN_M2_ENCA 35
#define PIN_M2_ENCB 36
#endif

/**
 * Other peripherals
 */
#ifdef esp32s3cam_lonelybinary
#define PIN_LED_WS2812 48
#define PIN_IR_LED 21
#endif