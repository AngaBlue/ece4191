// encoder.cpp
#include "encoder.h"
#include "pins.h"

// Global pointers to encoder objects (for ISR access)
Encoder* g_encoderM1 = nullptr;
Encoder* g_encoderM2 = nullptr;

Encoder encoderM1(PIN_M1_ENCA, PIN_M1_ENCB);
Encoder encoderM2(PIN_M2_ENCA, PIN_M2_ENCB);

// Static ISR functions
void IRAM_ATTR encoderM1ISR() {
    if (g_encoderM1) g_encoderM1->update();
}

void IRAM_ATTR encoderM2ISR() {
    if (g_encoderM2) g_encoderM2->update();
}

// Constructor
Encoder::Encoder(uint8_t pinA, uint8_t pinB)
    : pinA_(pinA), pinB_(pinB), count_(0) {}

// Initialize encoder pins and attach interrupts
void Encoder::begin() {
    pinMode(pinA_, INPUT_PULLUP);
    pinMode(pinB_, INPUT_PULLUP);

    // Assign global pointer for ISR
    if (this == &encoderM1) g_encoderM1 = this;
    if (this == &encoderM2) g_encoderM2 = this;

    // Attach static ISR
    if (this == &encoderM1)
        attachInterrupt(digitalPinToInterrupt(pinA_), encoderM1ISR, CHANGE);
    else if (this == &encoderM2)
        attachInterrupt(digitalPinToInterrupt(pinA_), encoderM2ISR, CHANGE);
}

long Encoder::getCount() const {
    return count_;
}

void Encoder::reset() {
    count_ = 0;
}

void Encoder::update() {
    bool a = digitalRead(pinA_);
    bool b = digitalRead(pinB_);
    if (a == b) {
        count_ += 1;
    } else {
        count_ -= 1;
    }
}


