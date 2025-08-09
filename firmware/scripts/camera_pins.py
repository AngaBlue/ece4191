# scripts/camera_pins.py
Import("env")

# Lonely Binary ESP32-S3 CAM (OV2640) pin map
# https://lonelybinary.com/cdn/shop/files/esp32-s3-camera.jpg?v=1744020115
PINS = dict(
    CAM_PIN_PWDN = -1,   # not connected
    CAM_PIN_RESET = -1,  # not connected

    CAM_PIN_SIOD = 4,
    CAM_PIN_SIOC = 5,

    CAM_PIN_VSYNC = 6,
    CAM_PIN_HREF  = 7,
    CAM_PIN_XCLK  = 15,
    CAM_PIN_PCLK  = 13,

    CAM_PIN_D7    = 16,  # CAM_Y9
    CAM_PIN_D6    = 17,  # CAM_Y8
    CAM_PIN_D5    = 18,  # CAM_Y7
    CAM_PIN_D4    = 12,  # CAM_Y6
    CAM_PIN_D3    = 10,  # CAM_Y5
    CAM_PIN_D2    = 8,   # CAM_Y4
    CAM_PIN_D1    = 9,   # CAM_Y3
    CAM_PIN_D0    = 11   # CAM_Y2 
)

env.Append(CPPDEFINES=[(k, v) for k, v in PINS.items()])
print(">> camera_pins.py: injected CAM_PIN_* macros:", PINS)
