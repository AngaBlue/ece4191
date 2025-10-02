#pragma once
#include <Arduino.h>

class IRLED {
public:
    IRLED(int pin, int freq = 5000, int resolution = 8);

    void begin();
    void onBrightness(uint8_t level); // set brightness (0–6)

private:
    int pin_;
    int freq_;
    int resolution_;
    int maxDuty_;
};
