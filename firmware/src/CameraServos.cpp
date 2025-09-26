#include <ESP32Servo.h>
#include <config.h>
#include <pins.h>

class CameraServos
{
public:
  void begin()
  {
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    this->pan.setPeriodHertz(SERVO_FREQ_HZ);
    this->tilt.setPeriodHertz(SERVO_FREQ_HZ);

    this->pan.attach(PIN_SERVO_PAN, SERVO_MIN_US, SERVO_MAX_US);
    this->tilt.attach(PIN_SERVO_TILT, SERVO_MIN_US, SERVO_MAX_US);
  }

  void move(int pan, int tilt)
  {
    this->pan.writeMicroseconds(angleToMicros(pan, SERVO_PAN_MIN_DEG, SERVO_PAN_MAX_DEG));
    this->tilt.writeMicroseconds(angleToMicros(tilt, SERVO_TILT_MIN_DEG, SERVO_TILT_MAX_DEG));
  }

private:
  Servo pan;
  Servo tilt;

  static inline int angleToMicros(int deg, int lo, int hi)
  {
    // Clamp
    deg = deg < lo ? lo : (deg > hi ? hi : deg);
    return SERVO_MIN_US + (int)((long long)deg * (SERVO_MAX_US - SERVO_MIN_US) / SERVO_RANGE_DEG);
  }
};
