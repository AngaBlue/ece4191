#include <Arduino.h>
#include "MotorControl.h"
#include "pins.h"

// PWM configuration
constexpr int PWM_FREQ_HZ = 20000;
constexpr int PWM_RES_BITS = 8;

void MotorControl::begin()
{
    // Attach pins (frequency and resolution set automatically)
    ledcAttach(PIN_ML_FOR, PWM_FREQ_HZ, PWM_RES_BITS);
    ledcAttach(PIN_ML_REV, PWM_FREQ_HZ, PWM_RES_BITS);
    ledcAttach(PIN_MR_FOR, PWM_FREQ_HZ, PWM_RES_BITS);
    ledcAttach(PIN_MR_REV, PWM_FREQ_HZ, PWM_RES_BITS);

    // Initialise PWM to zero
    ledcWrite(PIN_ML_FOR, 0);
    ledcWrite(PIN_ML_REV, 0);
    ledcWrite(PIN_MR_FOR, 0);
    ledcWrite(PIN_MR_REV, 0);
}

void MotorControl::applyPWM(int pinFwd, int pinRev, float value)
{
    // Map -1.0..1.0 normalised input → 0..255 PWM
    int pwm = (int)(fabs(value) * 255);

    if (value > 0)
    {
        ledcWrite(pinFwd, pwm);
        ledcWrite(pinRev, 0);
    }
    else if (value < 0)
    {
        ledcWrite(pinFwd, 0);
        ledcWrite(pinRev, pwm);
    }
    else
    {
        ledcWrite(pinFwd, 0);
        ledcWrite(pinRev, 0);
    }
}

void MotorControl::setVelocity(float left, float right)
{
    applyPWM(PIN_ML_FOR, PIN_ML_REV, left);
    applyPWM(PIN_MR_FOR, PIN_MR_REV, right);
}

void MotorControl::onMovement(float left, float right)
{
    left = constrain(left, -1.0f, 1.0f);
    right = constrain(right, -1.0f, 1.0f);
    this->setVelocity(left, right);
    Serial.printf("[UDP] Movement command: L=%.2f R=%.2f\n", left, right);
}
