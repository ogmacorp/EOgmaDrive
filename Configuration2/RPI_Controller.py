# ----------------------------------------------------------------------------
#  EOgmaDrive
#  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.
#
#  This copy of EOgmaDrive is licensed to you under the terms described
#  in the EOGMADRIVE_LICENSE.md file included in this distribution.
# ----------------------------------------------------------------------------

# -*- coding: utf-8 -*-

from time import sleep
from picamera import PiCamera
from PIL import Image, ImageFilter
from select import select

import sys, termios, atexit, subprocess
import numpy as np
import smbus
import eogmaneo
import cv2


_i2cAddr = 4
_system = None
_hierarchy = None
_piLeven = None
_camera = None
_image = None
_inputImage = None
_inputValue = None

steerChunkSize = int(6)
lineChunkSize = int(6)
lineSDRSizeDiv = int(1)

lineStepSize = lineChunkSize * 0.666
minLineLength = 6

hiddenWidth = 64
hiddenHeight = 32

sdrWidth = int(hiddenWidth / lineSDRSizeDiv)
sdrHeight = int(hiddenHeight / lineSDRSizeDiv)

numChunksInX = int(sdrWidth / lineChunkSize)
numChunksInY = int(sdrHeight / lineChunkSize)
numChunks = numChunksInX * numChunksInY
bitsPerChunk = lineChunkSize * lineChunkSize

#print("{}, {}, {}, {}".format(numChunksInX, numChunksInY, numChunks, bitsPerChunk))

lsd = cv2.createLineSegmentDetector(0)

# Capture as Yuv, but ignore UV channels
frame = np.empty((64*64 +((64*64)/2)), dtype=np.uint8)
y_data = np.empty((64, 64), dtype=np.uint8)

#fd = sys.stdin.fileno()
#new_term = termios.tcgetattr(fd)
#old_term = termios.tcgetattr(fd)

#new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)


#def setNormalTerm():
#    termios.tcsetattr(fd, termios.TCSAFLUSH, old_term)


#def setCursesTerm():
#    termios.tcsetattr(fd, termios.TCSAFLUSH, new_term)


#def kbhit():
#    dr,dw,de = select([sys.stdin], [], [], 0)
#    return dr != []


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def setupPiLeven():
    global _piLeven
    # Open i2c connection with PiLeven 
    # https://github.com/freetronics/PiLeven/wiki/i2c
    _piLeven = smbus.SMBus(1)
    print("Connecting to PiLeven (using addr {})".format(_i2cAddr))


def setupPiCamera():
    global _camera
    print("Initializing PiCamera...")
    _camera = PiCamera()
    _camera.resolution = (64, 64)
    _camera.rotation = 180
    _camera.framerate = 30
    #_camera.exposure_mode = 'sports'
    sleep(2)
    print('Camera parameters:')
    print('Modes: AWB {} DRC {} EXP {} Meter {}'.format(
        _camera.awb_mode, _camera.drc_strength,
        _camera.exposure_mode, _camera.meter_mode))
    print('ISO {} Exposure {} Shutter {}'.format(
        _camera.iso, _camera.exposure_speed, _camera.shutter_speed))
    print('Gain: Analog {} Digital {}'.format(
        _camera.analog_gain, _camera.digital_gain))
    print('Denoise: {}'.format(_camera.image_denoise))


def captureImage():
    global _camera, frame, y_data
    try:
        _camera.capture(frame, 'yuv', use_video_port=True, resize=(64, 64))
    except IOError:
        pass

    # Extract Y channel from the YUV420 capture
    y_data = frame[:64*64].reshape((64,64))


def captureAndFilterImage():
    global frame, y_data, _image, _camera
    try:
        _camera.capture(frame, 'yuv', use_video_port=True, resize=(64, 64))
    except IOError:
        pass

    # Extract Y channel from the YUV420 capture
    y_data = frame[:64*64].reshape((64,64))

    # Create a luminance Image from the numpy array
    _image = Image.fromstring('L', (y_data.shape[1], y_data.shape[0]), y_data.tostring())

    # Apply an edge-finding filter
    _image = _image.filter(ImageFilter.CONTOUR) #FIND_EDGES

    # Convert PIL image to numpy array
    y_data = np.asarray(_image)


def saveCameraImage():
    global y_data
    # Convert Luminance data to PIL image?
    camImage = Image.fromarray(y_data)
    # Save to tmp png
    camImage.save("/home/pi/Desktop/cameraImage.png")
    print('Saved camera image')


def savePredictedImage():
    global _hierarchy
    # Grab the predicted image fro the hierarchy
    luminance = np.asarray(_hierarchy.getPrediction(0), dtype=np.uint8)
    luminance = np.reshape(luminance, (64, 64))
    # Convert Luminance data to PIL image?
    _image = Image.fromarray(luminance)
    # Save to tmp png
    _image.save("/home/pi/Desktop/predictedImage.png")
    print('Saved predicted image')


def setupEOgmaNeo():
    global _system, _hierarchy, _inputImage, _inputValue
    
    print("Initializing EOgmaNeo::ComputeSystem")
    _system = eogmaneo.ComputeSystem(4)

    print("Initializing EOgmaNeo::Hierarchy")
    lds = eogmaneo.StdVecLayerDesc()
    numLayers = 6
    layerSize = 36
    for l in range(0, numLayers):
      ld = eogmaneo.LayerDesc()
      ld._width = layerSize
      ld._height = layerSize
      ld._forwardRadius = 9
      ld._backwardRadius = 9
      ld._ticksPerUpdate = 2
      ld._temporalHorizon = 2
      ld._alpha = 0.1
      ld._beta = 0.1
      ld._gamma = 0.01
      lds.push_back(ld)
      #layerSize = 16

    _hierarchy = eogmaneo.Hierarchy()
    _hierarchy.create([ ( hiddenWidth, hiddenHeight ), ( steerChunkSize, steerChunkSize ) ], [ lineChunkSize, steerChunkSize ], [ False, True ], lds, 41)

    _inputValue = eogmaneo.StdVeci(1 * 1)


def main():
    global _piLeven, _hierarchy, _system
    
    steering_val = 0.0
    loop = 0

    while True: #loop < 50:
        captureImage()
        #captureAndFilterImage()

        # Get the current steering value from the PiLeven
        try:
            _piLeven.write_byte_data(_i2cAddr, 97, 0)
        except IOError:
            print("i2c Error (write_byte, 97)")
            # Restart i2c bus
            subprocess.call(['i2cdetect', '-y', '1'])

        try:
            steering_val = int(_piLeven.read_byte(_i2cAddr))
        except IOError:
            print("i2c Error (read_byte, 97)")
            # Restart i2c bus
            subprocess.call(['i2cdetect', '-y', '1'])

        steering_val = clamp(int(steering_val), 30, 62)
        steering_val = (float(steering_val) - 46.0) / 16.0
        steering_val = (steering_val * 0.5 + 0.5) * (steerChunkSize * steerChunkSize - 1) + 0.5
        _inputValue[0] = int(steering_val)
        #print("{}".format(_inputValue[0]))

        lines = lsd.detect(y_data)

        rotSDR = numChunks*[int(0)]

        chunkResponses = numChunks*[-99999.0]

        # Assign lines to SDR
        if lines[0] != None:
            for l in lines[0]:
                bpt = l[0][0:2]
                ept = l[0][2:4]

                delta = ept - bpt

                mag = np.sqrt(delta[0] * delta[0] + delta[1] * delta[1])

                if mag < minLineLength:
                    continue

                response = mag

                delta = lineStepSize * delta / np.maximum(0.0001, mag)

                angle = np.arctan2(delta[1], delta[0])

                steps = int(mag / lineStepSize)

                p = bpt

                for s in range(steps):
                    # Fill
                    cx = min(numChunksInX - 1, max(0, int(p[0] / lineSDRSizeDiv / lineChunkSize)))
                    cy = min(numChunksInY - 1, max(0, int(p[1] / lineSDRSizeDiv / lineChunkSize)))

                    chunkIndex = cx + cy * numChunksInX

                    if response > chunkResponses[chunkIndex]:
                        chunkResponses[chunkIndex] = response

                        rotSDR[chunkIndex] = int(angle / (np.pi * 2.0) * (bitsPerChunk - 1)) % bitsPerChunk

                        if rotSDR[chunkIndex] < 0:
                            rotSDR[chunkIndex] += bitsPerChunk

                    # Step
                    p += delta

        _hierarchy.step([rotSDR, _inputValue], _system, True)

        predicted_val = _hierarchy.getPrediction(1)[0]
        predicted_val = predicted_val / float(steerChunkSize * steerChunkSize - 1) * 2.0 - 1.0
        predicted_val = float(predicted_val * 16.0 + 46.0)

        # Clamp to valid values for the front steering servo
        predicted_val = clamp(int(predicted_val), 30, 62)
        #print('{}'.format(predicted_val))

        # Send the predicted steering value to the PiLeven
        try:
            _piLeven.write_byte_data(_i2cAddr, 99, int(predicted_val))
        except IOError:
            print("i2c Error (write_byte, 99)")
            # Restart i2c bus
            subprocess.call(['i2cdetect', '-y', '1'])

        #throttle_val = float(_piLeven.read_byte_data(_i2cAddr, 98))

        loop += 1

        if loop%10 == 0:
            print("{}: S[{}] P[{}]".format(loop, steering_val, predicted_val))
            #print("Throttle: {}".format(throttle_val))

        #if kbhit():
        #    key = sys.stdin.read(1)
        #    if key == 's':
        #        saveCameraImage()
        #        #savePredictedImage()
        #        
        #    if key == '\x1b': #Escape
        #        break

    if (_piLeven != None):
        _piLeven.close()

    print("Steer: {}  -  Predicted: {}"
          .format(steering_val, predicted_val))


profilingEnabled = False

if __name__ == '__main__':
    #atexit.register(setNormalTerm)
    #setCursesTerm()

    setupPiLeven()
    setupPiCamera()
    setupEOgmaNeo()

    print("Setup complete.")

    if profilingEnabled is True:
        # http://softwaretester.info/python-profiling-with-pycharm-community-edition/
        import cProfile, pstats
        cProfile.run("main()", "{}.profile".format(__file__))
        # Replaced by snakeviz
        #s = pstats.Stats("{}.profile".format(__file__))
        #s.strip_dirs()
        #s.sort_stats("ncalls").print_stats(25)
        print('Run \'snakeviz {}.profile\' to visualize profiling'.format(__file__))
    else:
        main()
