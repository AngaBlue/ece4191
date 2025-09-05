# Development
## PlatformIO
PlatformIO is a development IDE extension that works inside of VSCode.  This allows you to use an editor that you're familiar with while also providing compiling, debugging and serial connections to MCUs.  Install the PlatformIO extension and ensure you have the `/firmware` directory open as your current workspace to get started.

PlatformIO should prompt you to install all the dependencies this project needs.

# Uploading Firmware
1. On the status bar at the bottom of the VSCode window, select your port.
2. Select the board.
3. Press the -> (right facing arrow) button to build and upload.

## Lonely Binary
Once external power has been disconnected, the firmware should be uploaded via the UART port.

![ESP32 S3 Pinout](https://lonelybinary.com/cdn/shop/files/esp32-s3-camera.jpg?v=1744020115)
