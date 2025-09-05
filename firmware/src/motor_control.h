// motor_control.h
#pragma once
#include "pid_controller.h"
#include "encoder.h"

class MotorControl {
public:
    void begin();
    void updateVelocity();
    void setVelocityOpenLoop(float leftNormalized, float rightNormalized); // direct PWM test mode
    void setVelocity(float left_normalized, float right_normalized);
    float getVelocityM1() const;
    float getVelocityM2() const;

private:
    static constexpr float CPR_GEARBOX = 50*380;
    static constexpr float MAX_RPM = 100.0f;

    unsigned long lastVelocityTime = 0;
    long lastEncoderCountM1 = 0;
    long lastEncoderCountM2 = 0;

    float velocityRPM_M1 = 0.0f;
    float velocityRPM_M2 = 0.0f;

    PIDController pidM1{20.0f, 5.0f, 1.0f, 0.1f};
    PIDController pidM2{20.0f, 5.0f, 1.0f, 0.1f};

    void setupPWM();
    void applyPWM(int pwmChannelFwd, int pwmChannelRev, int pwmValue, float direction);
};
