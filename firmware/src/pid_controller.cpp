// pid_controller.cpp
#include "pid_controller.h"
#include <algorithm>

PIDController::PIDController(float kp, float ki, float kd, float dt)
    : kp_(kp), ki_(ki), kd_(kd), dt_(dt), integral_(0), last_error_(0) {}

int PIDController::update(float setpoint, float measured) {
    float error = setpoint - measured;
    integral_ += error * dt_;

    // Clamp integral to avoid windup
    if (integral_ > integral_limit_) integral_ = integral_limit_;
    else if (integral_ < -integral_limit_) integral_ = -integral_limit_;

    float derivative = (error - last_error_) / dt_;
    float output = kp_ * error + ki_ * integral_ + kd_ * derivative;
    last_error_ = error;

    // Clamp output to PWM range 0-255
    output = clamp<float>(output, 0.0f, 255.0f);
    return static_cast<int>(output);
}
