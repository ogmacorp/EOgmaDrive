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

#define COM_ADDRESS 0xF0F0F0F0D5LL

#define STEER_BYTE_INDEX 0
#define DRIVE_BYTE_INDEX 1
#define MODE_BYTE_INDEX 2

#define TOTAL_BYTES 3

#define BYTE_INV_F 0.00392f

RF24 radio(9, 10);

#define ATTEMPT_DELAY 10
#define MAX_ATTEMPTS 100

byte steerB = 127;
byte driveB = 127;
byte modeB = 0;

//int counter = 0;

void setup() {
    Serial.begin(115200);

    //printf_begin();

    radio.begin();

    radio.setRetries(5, 5);

    //radio.setChannel(2);

    radio.setPayloadSize(TOTAL_BYTES);

    radio.openWritingPipe(COM_ADDRESS);

    //radio.printDetails();
}

void loop() {
    while (Serial.available() >= TOTAL_BYTES) {
        steerB = Serial.read();
        driveB = Serial.read();
        modeB = Serial.read();
    }

    //steerB = (byte)(sinf(counter * 0.1f) * 125 + 127);
    byte txData[TOTAL_BYTES];

    txData[STEER_BYTE_INDEX] = steerB;// *reinterpret_cast<byte*>(&serialData[STEER_BYTE_INDEX]);
    txData[DRIVE_BYTE_INDEX] = driveB;// *reinterpret_cast<byte*>(&serialData[DRIVE_BYTE_INDEX]);
    txData[MODE_BYTE_INDEX] = modeB;// *reinterpret_cast<byte*>(&serialData[MODE_BYTE_INDEX]);

    radio.writeBlocking(txData, TOTAL_BYTES, 50);
    //counter++;

    delay(10);
}
