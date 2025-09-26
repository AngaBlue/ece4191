#pragma once
#include <ESP32Servo.h>
#include <stdint.h>

class CameraServos
{
public:
  void begin();
  void move(int pan, int tilt);
  void onCamera(uint8_t pan, uint8_t tilt);

private:
  Servo pan;
  Servo tilt;

  inline int angleToMicros(int deg, int hi, int lo);
};
