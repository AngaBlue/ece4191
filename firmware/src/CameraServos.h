#pragma once
#include <ESP32Servo.h>

class CameraServos
{
public:
  void begin();
  void move(int pan, int tilt);
  void onCamera(int pan, int tilt);

private:
  Servo pan;
  Servo tilt;

  inline int angleToMicros(int deg, int hi, int lo);
};
