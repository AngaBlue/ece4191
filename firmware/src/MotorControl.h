#pragma once

class MotorControl
{
public:
    void begin();
    void setVelocity(float left, float right);
    void onMovement(float left, float right);

private:
    void applyPWM(int pinFwd, int pinRev, float value);
};
