#pragma once
#include <ESP32Servo.h>

class CameraServos
{
public:
  void begin();

  void move(int panDeg, int tiltDeg);

private:
  Servo pan;
  Servo tilt;

  inline int angleToMicros(int deg, int hi, int lo);
};
