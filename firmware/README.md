# Development
## PlatformIO
PlatformIO is a development IDE extension that works inside of VSCode.  This allows you to use an editor that you're familiar with while also providing compiling, debugging and serial connections to MCUs.  Install the PlatformIO extension and ensure you have the `/firmware` directory open as your current workspace to get started.

# Uploading Firmware
Currently, I have been able to get the firmware uploaded via UART.

![ESP32 S3 Pinout](https://lonelybinary.com/cdn/shop/files/esp32-s3-camera.jpg?v=1744020115)

# Reading Video Stream
To read the video stream over RTSP, I recommend using `ffmpeg`:

```bash
ffplay -rtsp_transport udp -probesize 32 -analyzeduration 0 -sync ext -vf setpts=0 -fflags nobuffer -fflags discardcorrupt -flags low_delay -framedrop -avioflags direct rtsp://192.168.137.161:554/
```
