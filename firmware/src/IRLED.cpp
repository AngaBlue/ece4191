#include "IRLED.h"

const int DUTIES[7] = {0, 10, 50, 100, 150, 200, 255};

IRLED::IRLED(int pin, int freq, int resolution)
    : pin_(pin), freq_(freq), resolution_(resolution)
{
    maxDuty_ = (1 << resolution_) - 1; // e.g. 255 for 8-bit
}

void IRLED::begin()
{
    // Attach pin to PWM
    ledcAttach(pin_, freq_, resolution_);
    onBrightness(0);
}

void IRLED::onBrightness(uint8_t level)
{
    // Clamp
    if (level > 6)
        level = 6;

    int duty = DUTIES[level];
    ledcWrite(pin_, duty);

    Serial.printf("[UDP] IR Brightness command: Level=%d -> Duty=%d)\n", level, duty);
}
