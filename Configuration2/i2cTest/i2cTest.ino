/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

#include <Wire.h>

#define I2C_ADDR 4
#define LED_PIN 13

void setup() {
  Wire.begin(I2C_ADDR);
  Wire.onReceive(receiveEvent);
  pinMode(LED_PIN, OUTPUT);
}

volatile int blinks = 0;

void loop() {
  if (blinks > 0) {
    digitalWrite(LED_PIN, HIGH);
    delay(1000);
    digitalWrite(LED_PIN, LOW);
    delay(1000);
    blinks--;
  }
}

void receiveEvent(int numBytes) {
  blinks = Wire.read();
}
