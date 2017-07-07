/*
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
*/

#include <Wire.h>

typedef enum EState {
  WARM_UP = 0,
  TRAINING_MODE = 1,
  PREDICTION_MODE = 2
};

int state = WARM_UP;
unsigned long startTime = 0;
const long warmUpTime = 1000; //milliseconds

int ledPin = 13;

int i2cAddr = 4;            // Slave addr: 4
unsigned char i2cRxBufferLen;
unsigned char i2cRxBuffer[BUFFER_LENGTH];

int steeringInputPin  = 9;  // From RF unit
int steeringOutputPin = 8;  // To steering servo
int throttleInputPin  = 10; // From RF unit
int throttleOutputPin = 11; // To ESC unit

int currSteeringPinState = 0;
int prevSteeringPinState = 0;
int currThrottlePinState = 0;
int prevThrottlePinState = 0;

int steeringHiCount = 0;
int steeringLoCount = 0;
int totalSteeringCount = 0;

int throttleHiCount = 0;
int throttleLoCount = 0;
int totalThrottleCount = 0;

long actualSteeringValue = 45;
long predictedSteeringValue = 45;
long actualThrottleValue = 45;
long predictedThrottleValue = 45;


void setup() {
  startTime = millis();

  // Setup i2c interface with RPi
  Wire.begin(i2cAddr);
  Wire.onReceive(i2cReceiveEvent);
  Wire.onRequest(i2cTransmitEvent);

  // Setup UART to XBee
  Serial.begin(9600);
  Serial.println("");
  
  // Setup I/O pins
  //pinMode(steeringInputPin, INPUT);
  //pinMode(steeringOutputPin, OUTPUT);
  
  //pinMode(throttleInputPin, INPUT);
  //pinMode(throttleOutputPin, OUTPUT);
  
  // Use LED for debug
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
}


void loop() {
  // Grab input states
  prevSteeringPinState = currSteeringPinState;
  currSteeringPinState = digitalRead(steeringInputPin);
  
  // Throttle forwarding
  prevThrottlePinState = currThrottlePinState;
  currThrottlePinState = digitalRead(throttleInputPin);
  
  switch (state) {
    case WARM_UP:
      if ((millis() - startTime) >= warmUpTime) {
        // Tell Pi-Top warm up is over
        Serial.println("Warm-up complete");
        digitalWrite(ledPin, HIGH);

        state = TRAINING_MODE;
        Serial.println("Mode: Training");
      }
      break;
      
    case TRAINING_MODE:
      // Count pin states
      if (currSteeringPinState == 1)
        steeringHiCount++;
      else
        steeringLoCount++;

      if (currThrottlePinState == 1)
        throttleHiCount++;
      else
        throttleLoCount++;

      // Capture low state transitions
      if (currSteeringPinState == 1 && prevSteeringPinState == 0) {
        actualSteeringValue = steeringHiCount;
        totalSteeringCount = steeringHiCount;
        steeringHiCount = 0;
      }

      if (currThrottlePinState == 1 && prevThrottlePinState == 0) {
        actualThrottleValue = throttleHiCount;
        totalThrottleCount = throttleHiCount;
        throttleHiCount = 0;
      }

      // Capture high state transitions
      if (currSteeringPinState == 0 && prevSteeringPinState == 1) {
        totalSteeringCount += steeringLoCount;
        steeringLoCount = 0;
      }

      if (currThrottlePinState == 0 && prevThrottlePinState == 1) {
        totalThrottleCount += throttleLoCount;
        throttleLoCount = 0;
      }

      // Forward to steering servo and ESC
      digitalWrite(steeringOutputPin, currSteeringPinState);
      digitalWrite(throttleOutputPin, currThrottlePinState);
      break;

    case PREDICTION_MODE:
      if (totalSteeringCount <= predictedSteeringValue) {
        steeringHiCount++;
        digitalWrite(steeringOutputPin, HIGH);
      }
      else {
        steeringLoCount++;
        digitalWrite(steeringOutputPin, LOW);
      }
        
      totalSteeringCount++;
      if (totalSteeringCount > 308)
        totalSteeringCount = 0;

      digitalWrite(throttleOutputPin, currThrottlePinState);
      break;
  }
}

void i2cReceiveEvent(int numBytes) {
  i2cRxBufferLen = (numBytes <= BUFFER_LENGTH) ? numBytes : BUFFER_LENGTH;
  
  for (int i = 0; i < i2cRxBufferLen; i++) {
    // get the byte sent from the RPi
    i2cRxBuffer[i] = Wire.read();
  }
 
  if (i2cRxBuffer[0] == 97) { //'a'
  }
  else
  if (i2cRxBuffer[0] == 98) { //'b'
  }
  else
  if (i2cRxBuffer[0] == 99) { //'c'
    predictedSteeringValue = i2cRxBuffer[1] | i2cRxBuffer[2]<<8;
  }
  else
  if (i2cRxBuffer[0] == 100) { //'d'
    predictedThrottleValue = i2cRxBuffer[1] | i2cRxBuffer[2]<<8;
  }
}

void i2cTransmitEvent() {
  if (i2cRxBuffer[0] == 97) { //'a'
    Wire.write(actualSteeringValue);
  }
  else
  if (i2cRxBuffer[0] == 98) { //'b'
    Wire.write(actualThrottleValue);
  }
}

// Check for XBee serial input (from Pi-Top)
void serialEvent() {
  char inChar = 0;

  while (Serial.available()) {
    // get the new byte:
    inChar = (char)Serial.read(); 
  }
  
  if (inChar == 't' || inChar == 'T') {
    state = TRAINING_MODE;
    Serial.println("Mode: Training");
    digitalWrite(ledPin, HIGH);
  }
  if (inChar == 'p' || inChar == 'P') {
    predictedSteeringValue = actualSteeringValue;
    totalSteeringCount = 0;
    state = PREDICTION_MODE;
    Serial.println("Mode: Prediction");
    digitalWrite(ledPin, LOW);
  }
  if (inChar == 's' || inChar == 'S') {
    Serial.print("Steering: A=");
    Serial.print(actualSteeringValue);
    Serial.print(" P=");
    Serial.print(predictedSteeringValue);
    Serial.print(" Throttle: A=");
    Serial.print(actualThrottleValue);
    Serial.print(" P=");
    Serial.println(predictedThrottleValue);
  }
  if (inChar == 'v' || inChar == 'V') {
    Serial.print("Steering: [");
    Serial.print(steeringHiCount);
    Serial.print(", ");
    Serial.print(steeringLoCount);
    Serial.print("], ");
    Serial.print(totalSteeringCount);
    Serial.print(" Throttle: [");
    Serial.print(throttleHiCount);
    Serial.print(", ");
    Serial.print(throttleLoCount);
    Serial.print("], ");
    Serial.println(totalThrottleCount);
  }
}

