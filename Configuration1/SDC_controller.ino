/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

#include <RF24_config.h>
#include <RF24.h>
#include <nRF24L01.h>
#include <printf.h>
#include <Servo.h>

#define COM_ADDRESS 0xF0F0F0F0D5LL

#define STEER_BYTE_INDEX 0
#define DRIVE_BYTE_INDEX 1
#define MODE_BYTE_INDEX 2

#define TOTAL_BYTES 3

#define BYTE_INV_F 0.00392f

RF24 radio(9, 10);

Servo steeringServo;
Servo drivingServo;

int targetSteer = 1500;
int targetDrive = 1500;

byte rxBuffer[TOTAL_BYTES];

#define MAX_ATTEMPTS 500

int attempt = 0;

byte steer = 127;
byte drive = 127;
byte mode = 0;

void setup() {
    Serial.begin(115200);
    //printf_begin();

    steeringServo.attach(3);
    drivingServo.attach(2);

    radio.begin();

    radio.setRetries(5, 5);

    radio.setPayloadSize(TOTAL_BYTES);

    //radio.setChannel(2);

    radio.openReadingPipe(1, COM_ADDRESS);
    
    radio.startListening();

    //radio.printDetails();
}

void loop() {
    if (radio.available()) {
        while (radio.available())
            radio.read(rxBuffer, TOTAL_BYTES);

        Serial.write(rxBuffer[STEER_BYTE_INDEX]);
        Serial.write(rxBuffer[DRIVE_BYTE_INDEX]);
        Serial.write(rxBuffer[MODE_BYTE_INDEX]);
    }

    if (Serial.available() >= TOTAL_BYTES - 1) {
        steer = Serial.read();
        drive = Serial.read();

        // Clear any remainder
        while (Serial.available())
            Serial.read();

        attempt = 0;
    }
    else {
        if (attempt < MAX_ATTEMPTS)
            attempt++;
    }

    // Stop driving if connection is lost
    if (attempt < MAX_ATTEMPTS) {
        targetSteer = 2000 - (int)((float)(steer) * BYTE_INV_F * 1000.0f);
        targetDrive = (int)((float)(drive) * BYTE_INV_F * 1000.0f) + 1000;
    }
    else {
        targetSteer = 1500;
        targetDrive = 1500;
    }

    steeringServo.writeMicroseconds(targetSteer);
    drivingServo.writeMicroseconds(targetDrive);

    delay(1);
}
