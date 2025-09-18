// pid_controller.h
#pragma once

class PIDController
{
public:
    PIDController(float kp, float ki, float kd, float dt);

    int update(float setpoint, float measured);

private:
    float kp_;
    float ki_;
    float kd_;
    float dt_;
    float integral_;
    float last_error_;
    static constexpr float integral_limit_ = 1000.0f;
};

template <typename T>
T clamp(T val, T minVal, T maxVal)
{
    return (val < minVal) ? minVal : (val > maxVal) ? maxVal
                                                    : val;
}
