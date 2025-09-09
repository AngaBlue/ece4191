// motor_control.cpp
#include <Arduino.h> // Must be first for ESP32 functions
#include "motor_control.h"
#include "pins.h"

// PWM configuration
constexpr int PWM_FREQ_HZ = 20000;
constexpr int PWM_RES_BITS = 8;

void MotorControl::begin()
{
    setupPWM();
}

void MotorControl::setupPWM()
{
    // Attach pins (frequency and resolution set automatically)
    ledcAttach(PIN_M1_IN1, PWM_FREQ_HZ, PWM_RES_BITS);
    ledcAttach(PIN_M1_IN2, PWM_FREQ_HZ, PWM_RES_BITS);
    ledcAttach(PIN_M2_IN1, PWM_FREQ_HZ, PWM_RES_BITS);
    ledcAttach(PIN_M2_IN2, PWM_FREQ_HZ, PWM_RES_BITS);

    // Initialize PWM to zero
    ledcWrite(PIN_M1_IN1, 0);
    ledcWrite(PIN_M1_IN2, 0);
    ledcWrite(PIN_M2_IN1, 0);
    ledcWrite(PIN_M2_IN2, 0);
}

void MotorControl::applyPWM(int pinFwd, int pinRev, int pwmValue, float direction)
{
    if (direction > 0)
    {
        ledcWrite(pinFwd, pwmValue);
        ledcWrite(pinRev, 0);
    }
    else if (direction < 0)
    {
        ledcWrite(pinFwd, 0);
        ledcWrite(pinRev, pwmValue);
    }
    else
    {
        ledcWrite(pinFwd, 0);
        ledcWrite(pinRev, 0);
    }
}

void MotorControl::setVelocity(float leftNormalized, float rightNormalized)
{
    updateVelocity();

    // Compute PWM from PID (assuming PID returns int in 0–255)
    int pwmM1 = pidM1.update(leftNormalized * MAX_RPM, velocityRPM_M1);
    int pwmM2 = pidM2.update(rightNormalized * MAX_RPM, velocityRPM_M2);

    // Apply PWM to channels
    applyPWM(PIN_M1_IN1, PIN_M1_IN2, pwmM1, leftNormalized);
    applyPWM(PIN_M2_IN1, PIN_M2_IN2, pwmM2, rightNormalized);

    Serial.printf("Set velocities L: %.2f R: %.2f, PWM L: %d R: %d\n",
                  leftNormalized, rightNormalized, pwmM1, pwmM2);
}

// New open-loop mode (direct PWM test)
void MotorControl::setVelocityOpenLoop(float leftNormalized, float rightNormalized)
{
    // Map -1.0..1.0 normalized input → 0..255 PWM
    int pwmM1 = (int)(fabs(leftNormalized) * 255);
    int pwmM2 = (int)(fabs(rightNormalized) * 255);

    applyPWM(PIN_M1_IN1, PIN_M1_IN2, pwmM1, leftNormalized);
    applyPWM(PIN_M2_IN1, PIN_M2_IN2, pwmM2, rightNormalized);

    Serial.printf("[Open-loop] L: %.2f → PWM %d, R: %.2f → PWM %d\n",
                  leftNormalized, pwmM1, rightNormalized, pwmM2);
}

float MotorControl::getVelocityM1() const { return velocityRPM_M1; }
float MotorControl::getVelocityM2() const { return velocityRPM_M2; }
