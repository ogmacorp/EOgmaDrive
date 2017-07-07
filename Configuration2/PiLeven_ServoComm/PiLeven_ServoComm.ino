/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

// Servo pass-through and Serial communications,
// using the Freetronics PiLevel RPI Hat
// https://www.freetronics.com.au/pages/pileven-getting-started-guide

#include <Wire.h>

int i2cAddr = 4;
int steering_pin1 = 10; // Connected to D10 (from RF unit)
int steering_pin2 = 9;  // Connected to D9  (to steering servo)


void setup() {
  // Setup XBee
  Serial.begin(9600);
  
  // Setup Pi comm (via i2c)
  Wire.begin(i2cAddr);
  Wire.onReceive(i2cReceiveEvent);
  
  // Setup input pin
  pinMode(steering_pin1, INPUT);

  // Setup output pin
  pinMode(steering_pin2, OUTPUT);
}

int steering_value = 0;
int steering_count = 0;
int currPinState = 0;
int prevPinState = 0;

void loop() {
  // Grab input state
  prevPinState = currPinState;
  currPinState = digitalRead(steering_pin1);
  
  // Forward to steering servo
  digitalWrite(steering_pin2, currPinState);

  // Count high state
  if (currPinState == 1)
    steering_count++;  

  // Capture low state transition
  if (currPinState == 1 && prevPinState == 0) {
    steering_value = steering_count;
    steering_count = 0;
  }
}

// XBee comm
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    if (inChar == 99) {
      Serial.write(66);
      Serial.write((steering_value&0x000000ff)>>0);
      Serial.write((steering_value&0x0000ff00)>>8);
      Serial.write((steering_value&0x00ff0000)>>16);
      Serial.write((steering_value&0xff000000)>>24);
      Serial.write(99);
      Serial.flush();
      break;
    }
  }
}

// Pi comm
void i2cReceiveEvent(int numBytes) {
  int in = Wire.read();
  
  if (in == 99) {
    Wire.write(66);
    Wire.write(steering_value);
    Wire.write(99);
  }
}
