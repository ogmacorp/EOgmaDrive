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
import pygame.surface
import pygame.joystick
import explorerhat

# Setup PyGame and create the link to the Steam controller

os.environ["SDL_VIDEODRIVER"] = "dummy"

signal.signal(signal.SIGINT, signal.default_int_handler)

pygame.init()
os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.display.init()

pygame.joystick.quit()
pygame.joystick.init()

joystick_count = pygame.joystick.get_count()

if joystick_count < 1:
    print("No joysticks found. sc-xbox.py not running?")
    sys.exit()

print("Found " + str(joystick_count) + " joysticks.")

joy = pygame.joystick.Joystick(0)
joy.init()

# Global control variables

trimming = 0.2
powerScalar = 0.5

steer = 0
drive = 0

endProg = False

# Loop until the 'A' button is pressed
print("")
print("Controls:")
print("The `A` button exits the script.")
print("The joystick controls left/right steering.")
print("Left trigger applies forward drive.")
print("Right trigger applies backward drive.")

while not endProg:
    try:
        timeStart = pygame.time.get_ticks()

        for event in pygame.event.get():
            # A button pressed?
            if event.type == pygame.JOYBUTTONDOWN and joy.get_button(0) == 1:
                endProg = True

        # Left and Right triggers
        joydrive = (joy.get_axis(5) * 0.5 + 0.5) - (joy.get_axis(2) * 0.5 + 0.5)

        # Joystick steering control
        joysteer = joy.get_axis(0)

        steer = joysteer
        drive = joydrive

        left = min(1.0, max(-1.0, drive * 0.5 - drive * steer * 0.5))
        right = min(1.0, max(-1.0, drive * 0.5 + drive * steer * 0.5))

        sendLeftMotor = left
        sendRightMotor = right

        trimMulLeft = 1.0 - max(0.0, -trimming)
        trimMulRight = 1.0 - max(0.0, trimming)

        explorerhat.motor[0].speed(int(sendLeftMotor * trimMulLeft * powerScalar * 100))
        explorerhat.motor[1].speed(-int(sendRightMotor * trimMulRight * powerScalar * 100))

        timeEnd = pygame.time.get_ticks()

        deltaTime = timeEnd - timeStart

        pygame.time.delay(max(0, 100 - deltaTime))
        
    except KeyboardInterrupt:
        endProg = True
        break

pygame.quit()
