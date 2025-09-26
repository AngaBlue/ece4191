#include <ESP32Servo.h>

class CameraServos
{
public:
  void begin();

  void move(int panDeg, int tiltDeg);

private:
  Servo pan;
  Servo tilt;

  static inline int angleToMicros(int deg);
};
