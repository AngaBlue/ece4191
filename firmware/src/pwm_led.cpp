#include "pwm_led.h"

PwmLed::PwmLed(int pin, int freq, int resolution)
    : pin_(pin), freq_(freq), resolution_(resolution)
{
    maxDuty_ = (1 << resolution_) - 1; // e.g. 255 for 8-bit
}

void PwmLed::begin()
{
    // Attach pin to PWM
    ledcAttach(pin_, freq_, resolution_);
    onBrightness(0); // start off
}

void PwmLed::onBrightness(uint8_t level)
{
    if (level > 6)
        level = 6; // clamp to 0–6

    // Map 0–6 → 0–maxDuty
    int duty = map(level, 0, 6, 0, maxDuty_);
    ledcWrite(pin_, duty);

    Serial.printf("LED brightness level %d (duty %d)\n", level, duty);
}
