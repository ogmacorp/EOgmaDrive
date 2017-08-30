# ----------------------------------------------------------------------------
#  EOgmaDrive
#  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.
#
#  This copy of EOgmaDrive is licensed to you under the terms described
#  in the EOGMADRIVE_LICENSE.md file included in this distribution.
# ----------------------------------------------------------------------------

# -*- coding: utf-8 -*-

import sys
import os
import signal
import pygame
import picamera
import pygame.surface
import pygame.joystick
import numpy as np
import struct
import re
import os.path
import eogmaneo
import time
import explorerhat
import cv2

loadExisting = len(sys.argv) > 1 and sys.argv[1] == "load"

if loadExisting:
    print("Called with load. Reloading a saved hierarchy, if it exists.")

######################
# Setup PyGame

os.environ["SDL_VIDEODRIVER"] = "dummy"
signal.signal(signal.SIGINT, signal.default_int_handler)

pygame.init()
os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.display.init()

pygame.joystick.quit()
pygame.joystick.init()

joystick_count = pygame.joystick.get_count()

if joystick_count < 1:
    print("No joysticks found.")

    sys.exit()

print("Found " + str(joystick_count) + " joysticks.")

joy = pygame.joystick.Joystick(0)
joy.init()

######################
# Setup PiCamera

camera = picamera.PiCamera()

camWidth = 64
camHeight = 48

camera.resolution = (camWidth, camHeight)
camera.framerate = 24
#camera.rotation = 180

time.sleep(2)

######################
# Setup EOgmaNeo

esystem = eogmaneo.ComputeSystem(4)

ld = 2 * [ eogmaneo.LayerDesc() ]

for l in range(0, len(ld)):
    ld[l]._width = 24
    ld[l]._height = 24
    ld[l]._chunkSize = 6

    ld[l]._forwardRadius = 9
    ld[l]._backwardRadius = 9

    ld[l]._ticksPerUpdate = 2
    ld[l]._temporalHorizon = 2
    ld[l]._alpha = 0.1
    ld[l]._beta = 0.1
    ld[l]._delta = 0.0

resizedWidth = 64
resizedHeight = 48

motorChunkSize = int(5)
hiddenChunkSize = int(6)
SDRSizeDiv = int(1)

hiddenWidth = resizedWidth
hiddenHeight = int(resizedHeight * 2 / 3) - 3

sdrWidth = int(hiddenWidth / SDRSizeDiv)
sdrHeight = int(hiddenHeight / SDRSizeDiv)

numChunksInX = int(sdrWidth / hiddenChunkSize)
numChunksInY = int(sdrHeight / hiddenChunkSize)
numChunks = numChunksInX * numChunksInY
bitsPerChunk = hiddenChunkSize * hiddenChunkSize

print("SDR Width x Height: " + str(sdrWidth) + " " + str(sdrHeight))

h = eogmaneo.Hierarchy()
enc = eogmaneo.ImageEncoder()

# Hierarchy and pre-encoder saved state filenames
saveName = "SDCSaveSobel.eohr"
saveNameEnc = "SDCSaveEncSobel.txt"

if os.path.isfile(saveName) and loadExisting:
    print("Loading existing hierarchy...")

    h.load(saveName)
    enc.load(saveNameEnc)

else:
    print("Creating new hierarchy...")

    h.create([(sdrWidth, sdrHeight), (motorChunkSize, motorChunkSize)], [hiddenChunkSize, motorChunkSize], [False, True], ld, 41)
    enc.create(hiddenWidth, hiddenHeight, sdrWidth, sdrHeight, hiddenChunkSize, 6, 1234)

print("Created pre-encoder and hierarchy.")

trainMode = True
enabled = False

trimming = 0.0
powerScalar = 0.5

targetSteer = 0.0
targetDrive = 0.0
targetMode = False

steer = 0
drive = 0
mode = 0

joymodePrev = False

saveImgPrev = False
saveHPrev = False
loadHPrev = False

imgIndex = 0

endProg = False

print("")
print("Controls:")
print("The `A` button toggles between training and prediction modes.")
print("The `B` button saves the current camera image.")
print("The `X` button saves the current state of the hierarchy.")
print("The `Y` button exits the script.")
print("")
print("The joystick controls left/right steering.")
print("Trigger buttons apply forward/backward drive.")

############################
# Loop until the 'Y' button is pressed

while not endProg:
    try:
        timeStart = pygame.time.get_ticks()

        ############################
        # Check Pygame for exit conditions

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and joy.get_button(3) == 1:
                endProg = True

            if event.type == pygame.QUIT:
                endProg = True

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            endProg = True

        ############################
        # Receive Steam controller data

        joydrive = (joy.get_axis(5) * 0.5 + 0.5) - (joy.get_axis(2) * 0.5 + 0.5)
        joysteer = joy.get_axis(0)

        joymode = joy.get_button(0)

        steer = joysteer
        drive = joydrive

        if joymode and not joymodePrev:
            mode = not mode

        joymodePrev = joymode

        moving = drive > 0.05

        training = not mode

        ############################
        # Grab an image from the camera

        visData = np.empty((camHeight, camWidth, 3), dtype=np.uint8)

        camera.capture(visData, "rgb", use_video_port=True)

        if resizedWidth != camWidth or resizedHeight != camHeight:
            visData = cv2.resize(visData, (resizedWidth, resizedHeight), interpolation=cv2.INTER_AREA)

        visData = visData[resizedHeight - int(hiddenHeight):, :, :]

        # Convert to grey scale
        visDataGrey = 0.333 * ((visData[:, :, 0].T / 255.0) + (visData[:, :, 1].T / 255.0) + (visData[:, :, 2].T / 255.0))

        # Apply optional Sobel filtering, and ravel to a 1D list
        filtered = visDataGrey.T.ravel().tolist()#eogmaneo.sobel(visDataGrey.T.ravel().tolist(), hiddenWidth, 0.0, esystem, 8)

        # Send the filtered camera image into the ImageEncoder
        useSDR = enc.activate(filtered, esystem)

        enc.learn(0.1, esystem)

        ############################
        # Create a sparse chunked representation from the steering and drive values
        left = min(1.0, max(-1.0, drive * 0.5 + drive * steer * 0.5))
        right = min(1.0, max(-1.0, drive * 0.5 - drive * steer * 0.5))

        motorSDR = [int((steer * 0.5 + 0.5) * (motorChunkSize * motorChunkSize - 1) + 0.5)]

        useMotorSDR = motorSDR

        # In inference mode, use the hierarchy next predicted steering values
        if not training:
            useMotorSDR = h.getPrediction(1)

        if not training or moving:
            h.step([useSDR, useMotorSDR], esystem, training and moving)

        sendLeftMotor = left
        sendRightMotor = right

        # In inference mode, use the hierarchy prediction to drive
        # the motors (instead of the steam controller)
        if not training:
            predMotorIndex = h.getPrediction(1)[0]

            drive = 0.65

            predSteer = predMotorIndex / float(motorChunkSize * motorChunkSize - 1) * 2.0 - 1.0

            sendLeftMotor = min(1.0, max(-1.0, drive * 0.5 + drive * predSteer * 0.5))
            sendRightMotor = min(1.0, max(-1.0, drive * 0.5 - drive * predSteer * 0.5))

        # Apply corrective trimming to the motor drive values
        trimMulLeft = 1.0 - max(0.0, -trimming)
        trimMulRight = 1.0 - max(0.0, trimming)

        # Set the speed of each motor
        explorerhat.motor[0].speed(int(sendLeftMotor * trimMulLeft * powerScalar * 100))
        explorerhat.motor[1].speed(-int(sendRightMotor * trimMulRight * powerScalar * 100))

        ############################

        # Save out the current camera image?
        if joy.get_button(1) and not saveImgPrev:
            cv2.imwrite("img" + str(int(imgIndex)) + ".png", visData[:, :, ::-1])

            print("Saved image.")

            imgIndex += 1

        # Save out the current state of the hierarchy?
        if joy.get_button(2) and not saveHPrev:
            print("Saving hierarchy...")

            h.save(saveName)
            enc.save(saveNameEnc)

            print("Saved hierarchy.")

        saveImgPrev = joy.get_button(1)
        saveHPrev = joy.get_button(2)

        timeEnd = pygame.time.get_ticks()

        deltaTime = timeEnd - timeStart

        pygame.time.delay(max(0, 100 - deltaTime))

    except KeyboardInterrupt:
        endProg = True
        break

pygame.quit()
