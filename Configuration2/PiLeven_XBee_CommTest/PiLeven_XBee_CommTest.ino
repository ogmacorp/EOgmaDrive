/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

#include <Wire.h>

void setup() {
  // Setup i2c interface with RPi
  Wire.begin(4); // Slave addr: 4
  Wire.onReceive(i2cReceiveEvent);
  Wire.onRequest(i2cTransmitEvent);

  // Setup UART to XBee
  Serial.begin(9600);
}

void loop() {
}

void i2cReceiveEvent(int numBytes) {
  for (int i = 0; i < numBytes; i++) {
    // get the byte sent from the RPi
    char inByte = Wire.read();
    
    // forward to XBee
    Serial.write(inByte);
  }
}

volatile char inChar = 0;

void i2cTransmitEvent() {
  Wire.write(inChar);
}

void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    inChar = (char)Serial.read(); 
    
    // forward to RPi
    //Wire.write(inChar);
  }
}

