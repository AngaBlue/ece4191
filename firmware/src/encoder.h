// encoder.h
#pragma once
#include <Arduino.h>

class Encoder {
public:
    Encoder(uint8_t pinA, uint8_t pinB);

    void begin();
    long getCount() const;
    void reset();

    void update(); // Call in ISR

private:
    uint8_t pinA_;
    uint8_t pinB_;
    volatile long count_;
};

extern Encoder encoderM1;
extern Encoder encoderM2;
