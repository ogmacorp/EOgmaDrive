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
from threading import Thread
from threading import Lock
from threading import Condition
from threading import Barrier
import os.path
from PIL import Image
import serial
import eogmaneo
import time
import cv2

trimming = 0.1

os.environ["SDL_VIDEODRIVER"] = "dummy"

def pygame_to_pil_img(pg_surface):
    imgstr = pygame.image.tostring(pg_surface, 'RGB')
    return Image.fromstring('RGB', pg_surface.get_size(), imgstr)

def pil_to_pygame_img(pil_img):
    imgstr = pil_img.tostring()
    return pygame.image.fromstring(imgstr, pil_img.size, 'RGB')

def matToVec(mat):
    return mat.flatten().astype(np.float32).tolist()

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))

endProg = False

signal.signal(signal.SIGINT, signal.default_int_handler)

camWidth = 64
camHeight = 64

steerChunkSize = 6

pygame.init()
pygame.joystick.init()

joystick_count = pygame.joystick.get_count()

if joystick_count < 1:
    print("No joysticks found.")

    sys.exit()

print("Found " + str(joystick_count) + " joysticks.")

joy = pygame.joystick.Joystick(0)
joy.init()

camera = picamera.PiCamera()

camera.resolution = (camWidth, camHeight)
camera.framerate = 24

#camera.start_preview()

time.sleep(2)

######################

ser = serial.Serial('/dev/serial/by-id/usb-Arduino_Srl_Arduino_Uno_556393038343514082D0-if00', 115200)

s = eogmaneo.ComputeSystem(4)

#lr = eogmaneo.LocalRegressor()

#lr.load("localregSave.txt")

ld = 4 * [ eogmaneo.LayerDesc() ]

for l in range(0, len(ld)):
    ld[l]._width = 36
    ld[l]._height = 36
    ld[l]._chunkSize = 6

    if l == 0:
        ld[l]._forwardRadius = 9
        ld[l]._backwardRadius = 9
    else:
        ld[l]._forwardRadius = 9
        ld[l]._backwardRadius = 9
        
    ld[l]._ticksPerUpdate = 2
    ld[l]._temporalHorizon = 2
    ld[l]._alpha = 0.04
    ld[l]._beta = 0.12
    ld[l]._gamma = 0.0

hiddenWidth = camWidth
hiddenHeight = int(camHeight / 2)

h = eogmaneo.Hierarchy()
h.create([ ( hiddenWidth, hiddenHeight ), ( steerChunkSize, steerChunkSize ) ], [ 6, steerChunkSize ], [ False, True ], ld, 41)

ce = eogmaneo.CornerEncoder()
ce.create(hiddenWidth, hiddenHeight, 6, 1)

trainMode = True
enabled = False

targetSteer = 0.0
targetDrive = 0.0
modeTicks = 0
reqModeTicks = 3
targetMode = False

speedMul = 0.25
capTime = 5.0
capTimer = 0.0
imgIndex = 0

steer = 0
drive = 0
mode = 0

joymodePrev = False

visDataGreyPrev = np.zeros((camHeight, hiddenHeight))

while not endProg:
    try:
        timeStart = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                endProg = True

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            endProg = True

        ############################

        # Receive data
        
        #print(steer)

        joydrive = (joy.get_axis(5) * 0.5 + 0.5) - (joy.get_axis(2) * 0.5 + 0.5)
        joysteer = joy.get_axis(0)

        joymode = joy.get_button(0)

        steer = joysteer
        drive = joydrive * speedMul

        if joymode and not joymodePrev:
            mode = not mode

        joymodePrev = joymode

        moving = drive > 0.036

        training = not mode
        
        ############################

        visData = np.empty((camHeight, camWidth, 3), dtype=np.uint8)

        camera.capture(visData, "rgb", use_video_port=True)

        visData = visData[0:int(hiddenHeight), :, :]   
        
        visDataGrey = 0.333 * ((visData[:,:,0].T / 255.0) + (visData[:,:,1].T / 255.0) + (visData[:,:,2].T / 255.0))

        visDataDelta = (visDataGrey - visDataGreyPrev) * 0.5 + 0.5

        visDataGreyPrev = visDataGrey
        #visDataR = matToVec(visData[:,:,0].T / 255.0)
        #visDataG = matToVec(visData[:,:,1].T / 255.0)
        #visDataB = matToVec(visData[:,:,2].T / 255.0)
        
        # Canny
        visDataGrey = visDataGrey.reshape((hiddenHeight, hiddenWidth))
        visDataGreyb = (visDataGrey * 255).astype(np.uint8)
        visDataEdgesb = cv2.Canny(visDataGreyb, 200, 300)
        visDataEdges = visDataEdgesb.astype(np.float32) / 255.0

        if capTimer >= capTime:
            capTimer = 0.0

            #cv2.imwrite("imgs/img" + str(int(imgIndex)) + ".png", visData[:,:,::-1])

            imgIndex += 1
        
        #lr.activate([ visDataR, visDataG, visDataB ], 0.01, s, 8)

        #lroutput = list(lr.getOutput()[0])

        # Threshold local regressor output
        #for i in range(len(lroutput)):
        #    lroutput[i] = float(lroutput[i] > 0.5)

        ce.activate(matToVec(visDataEdges), s, 2, 0.2, 16)

        ceoutput = ce.getHiddenStates(0)

        useSteerSDR = [ int((steer * 0.5 + 0.5) * (steerChunkSize * steerChunkSize - 1) + 0.5) ]

        if not training:
            useSteerSDR = h.getPrediction(1)
     
        h.step([ ceoutput, useSteerSDR ], s, training and moving)

        #print(h.getHiddenState(0))

        sendSteer = steer
        sendDrive = drive

        if not training:
            predSteerIndex = h.getPrediction(1)[0]
                
            sendSteer = min(1.0, max(-1.0, predSteerIndex / float(steerChunkSize * steerChunkSize - 1) * 2.0 - 1.0))
            #sendSteer = min(1.0, max(-1.0, re.reconstruct(h.getPrediction(1), s)[0]))
            #print(targetSteer)
            sendDrive = 0.164

        trimmedSteer = min(1.0, max(-1.0, sendSteer + trimming))

        ser.write(bytes([int((trimmedSteer * 0.5 + 0.5) * 255), int((sendDrive * 0.5 + 0.5) * 255)]))

        ############################

        timeEnd = pygame.time.get_ticks()

        deltaTime = timeEnd - timeStart

        if training and moving:
            capTimer += deltaTime * 0.001

        pygame.time.delay(max(0, 30 - deltaTime))
        
    except KeyboardInterrupt:
        endProg = True
        break

pygame.quit()
ser.close()
