// #include <Arduino.h>
// #include "motor_control.h"
// #include "encoder.h"
// #include "pins.h"

// // Create motor control object
// MotorControl motorControl;

// // Forward declare encoders from encoder.cpp
// extern Encoder encoderM1;
// extern Encoder encoderM2;

// void setup() {
//     Serial.begin(115200);
//     Serial.println("=== Encoder + Motor Test ===");

//     // Init encoders
//     encoderM1.begin();
//     encoderM2.begin();

//     // Init motor control
//     motorControl.begin();

//     // Give motors a short delay before starting
//     delay(2000);
//     Serial.println("Starting motors...");
// }

// void loop() {
//     // Run motors in open-loop
//     float leftCmd  = 0.5f;   // 50% forward power
//     float rightCmd = 0.5f;   // 50% forward power
//     motorControl.setVelocityOpenLoop(leftCmd, rightCmd);

//     // Update and print velocities every 500 ms
//     static unsigned long lastPrint = 0;
//     if (millis() - lastPrint > 500) {
//         long countM1 = encoderM1.getCount();
//         long countM2 = encoderM2.getCount();

//         motorControl.updateVelocity();

//         Serial.printf("Counts: M1=%ld, M2=%ld | Velocity: M1=%.2f RPM, M2=%.2f RPM\n",
//                       countM1, countM2,
//                       motorControl.getVelocityM1(),
//                       motorControl.getVelocityM2());

//         lastPrint = millis();
//     }
// }
