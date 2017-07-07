/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

#include <SoftwareSerial.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

void setup() {
  // Open serial communications
  Serial.begin(9600);
  while (!Serial)
    ; // wait for serial port to connect

  // Set the XBee data rate for the SoftwareSerial port
  xbeeSerial.begin(9600);
}

void loop() {
  // UART pass-through
  if (xbeeSerial.available()) {
    Serial.write(xbeeSerial.read());
  }
  if (Serial.available()) {
    xbeeSerial.write(Serial.read());
  }
}
