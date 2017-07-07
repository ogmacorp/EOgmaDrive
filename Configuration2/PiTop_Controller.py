# ----------------------------------------------------------------------------
#  EOgmaDrive
#  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.
#
#  This copy of EOgmaDrive is licensed to you under the terms described
#  in the EOGMADRIVE_LICENSE.md file included in this distribution.
# ----------------------------------------------------------------------------

# -*- coding: utf-8 -*-

import pygame
import serial

(SCREEN_WIDTH, SCREEN_HEIGHT) = (300, 200)
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

BACKGROUND_COLOUR = (32, 32, 32)

pygame.display.set_caption('EOgmaDrive Controller')

pygame.font.init()
FONT = pygame.font.SysFont("Arial", 20)


def display_mode(string, colour):
    """ Display centered text """
    text = FONT.render(string, True, colour)
    text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    SCREEN.blit(text, text_rect)


def main():
    """ Main function """
    port = serial.Serial(port="/dev/ttyACM0", baudrate=9600)
    if port._isOpen == False:
        print("Failed to open /dev/ttyACM0")
        pygame.quit()
        return

    training = True

    SCREEN.fill(BACKGROUND_COLOUR)
    display_mode(string="Mode: TRAINING", colour=(64, 64, 255))

    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                SCREEN.fill(BACKGROUND_COLOUR)

                if training:
                    training = False
                    port.write(b'P')
                    display_mode(string="Mode: PREDICTING",
                                 colour=(255, 64, 64))
                else:
                    training = True
                    port.write(b'T')
                    display_mode(string="Mode: TRAINING",
                                 colour=(64, 64, 255))

                pygame.display.flip()

    port.close()
    pygame.quit()


if __name__ == '__main__':
    main()
