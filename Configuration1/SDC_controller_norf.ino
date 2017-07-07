/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

#include <Servo.h>

#define COM_ADDRESS 0xF0F0F0F0D5LL

#define STEER_BYTE_INDEX 0
#define DRIVE_BYTE_INDEX 1
#define MODE_BYTE_INDEX 2

#define TOTAL_BYTES 2

#define BYTE_INV_F 0.00392f

Servo steeringServo;
Servo drivingServo;

int targetSteer = 1500;
int targetDrive = 1500;

byte steer = 127;
byte drive = 127;
byte mode = 0;

void setup() {
    Serial.begin(115200);
    //printf_begin();

    steeringServo.attach(3);
    drivingServo.attach(2);
}

void loop() {
    if (Serial.available() >= TOTAL_BYTES) {
        steer = Serial.read();
        drive = Serial.read();

        // Clear any remainder
        while (Serial.available())
            Serial.read();
    }

    // Stop driving if connection is lost
    targetSteer = 2000 - (int)((float)(steer)* BYTE_INV_F * 1000.0f);
    targetDrive = (int)((float)(drive)* BYTE_INV_F * 1000.0f) + 1000;

    steeringServo.writeMicroseconds(targetSteer);
    drivingServo.writeMicroseconds(targetDrive);

    delay(1);
}
