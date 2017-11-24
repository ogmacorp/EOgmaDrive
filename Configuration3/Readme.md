<!---
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
--->

# Configuration3 (uSDC)

[![Join the chat at https://gitter.im/ogmaneo/Lobby](https://img.shields.io/gitter/room/nwjs/nw.js.svg)](https://gitter.im/ogmaneo/Lobby)

As seen in the first issue of the [HackSpace magazine](https://hackspace.raspberrypi.org/issues/1) (December 2017), and as a project on [HackADay.io](https://hackaday.io/project/27173-a-self-driving-car-using-a-raspberry-pi-zero)

## Bill of Materials

The [BillOfMaterials.md](BillOfMaterials.md) file details all the items required before assembly.

## Hardware Assembly

Refer to the [AssemblyInstructions.md](AssemblyInstructions.md) file for a detailed description of the assembly steps.

## Software Installation

The [SoftwareInstallation.md](SoftwareInstallation.md) file contains all the steps required to install and test package dependencies.

## Control of the uSDC

There are two Python3 scripts included in this repository to test the uSDC:

- motorTest.py - A script to test the Explorer pHAT, Steam controller, and drive the uSDC around.
- main.py - The main script containing using the EOgmaNeo library. Allowing for learning, inference, and self-driving on the RPi ZeroW.

### Steam controller daemon

Both of the included python scripts require the Steam controller daemon to be running. After the daemon has been started, it emulates the Steam controller as a Xbox controller. PyGame can then connect to and obtain joystick and button information. The motorTest.py and main.py scripts can then make use of the controller to drive the uSDC around.

Starting the daemon requires the following bash command:

```bash
sudo python3 ~/steamcontroller/scripts/sc-xbox.py start
```

and the following command to stop the daemon:

```bash
sudo python3 ~/steamcontroller/scripts/sc-xbox.py stop
```

### motorTest python script

To test the Steam controller and Explorer pHAT motor driver, the following commands and script can be used:

```bash
cd ~/EOgmaDrive/Configuration3
sudo python3 ~/steamcontroller/scripts/sc-xbox.py start
sudo python3 motorTest.py
sudo python3 ~/steamcontroller/scripts/sc-xbox.py stop
```

Similar controls as used in the main.py script are used here:

- The joystick controls left or right steering,
- Trigger buttons apply forward/backward drive,
- The `A` button cleanly exits the script.

The `trimming` global variable allows for trimming of the forward/backward motion, so that applying motion using the triggers ensures that the uSDC travels in a straight line.

## The main python script

The `main.py` Python3 script is used for training (manual driving) and inference (self driving). All processing occurs on the Raspberry Pi ZeroW board.

It can be started using the following bash commands:

```bash
cd ~/EOgmaDrive/Configuration3
sudo python3 ~/steamcontroller/scripts/sc-xbox.py start
sudo python3 main.py
sudo python3 ~/steamcontroller/scripts/sc-xbox.py stop
```

The uSDC can then be controlled using the Steam controller with:

- The analogue joystick controls left or right steering.
- Trigger buttons apply forward/backward drive.
- The `A` button toggles between training and prediction modes.
- The `B` button saves the current camera image.
- The `X` button saves the current state of the hierarchy.
- The `Y` button exits the script.

If you train and save out the current state of the hierarchy, that saved state can be reloaded by starting the script with a `load` parameter. For example:

```bash
sudo python3 main.py load
```

**Note:** Saving the hierarchy to the a file on the SD card can take a minute or so to perform. Console text will announce when saving starts, and also when saving has completed.

If the uSDC doesn't travel in a straight line using one of the trigger buttons, a `trimming` global variable can be modified to compensate for any drift. For example this could be set to `trimming = 0.2`

An `RGB` image is captured from the camera module at each time step. This is converted into a grey scale image. And an EOgmaNeo pre-encoder (`ImageEncoder`) is used to transform the dense camera image into a sparse chunked representation, that alongside the current motor values, is sent into the EOgmaNeo predictive hierarchy.

When the `A` button is initially pressed the `training` global variable is toggled. And instead of using the Steam controller input to steer the uSDC and send values into the EOgmaNeo predictive hierarchy (training mode), the hierarchy's prediction of the next motor steering values are used (inference mode). Be aware that during inference mode a constant forward drive is applied to both motors. Pressing the `A` button again can toggle back to training mode.

## Testing the uSDC

Online learning only occurs within the `main.py` script and the EOgmaNeo predictive hierarchy when forward drive is active. To navigate around a track, a number of laps are required before the predictive hierarchy can confidently make steering predictions.

With learning only enabled during forward motion, it's possible to reverse out of steering mistakes made when driving around a track.

The more laps of a track that occur during training mode, the more confident the predictive hierarchy will be when switching to inference mode (that is, steering only use hierarchy output predictions and current camera input).

As seen in our YouTube video of the uSDC, we use an [InfiniTrax](http://infinitrax.com/product.php) modular track to perform more elaborate training and inference testing.

<a href="http://www.youtube.com/watch?feature=player_embedded&v=9GNbVkMb8Qw
" target="_blank"><img src="http://img.youtube.com/vi/9GNbVkMb8Qw/0.jpg" 
alt="World's Smallest Self-Driving Car - a Raspberry Pi Zero on wheels.." width="480" height="360" border="1"/></a>

The simplest way to check that everything is working is to perform the following:

1. Apply constant left/right steering.
1. Apply forward drive so that the uSDC spins on the spot.
1. After 30-60 seconds, release the joystick and trigger button.
1. Press the `A` button, and the uSDC should spin on the spot.
1. Press the `A` button again to toggle back to training mode.

Try the above but steering in the opposite direction. And test out saving and reloading of the hierarchy to see whether it remembers how to spin on the spot.

## License and Copyright

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />The work in this repository is licensed under the <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>. See the  [EOGMADRIVE_LICENSE.md](https://github.com/ogmacorp/EOgmaDrive/blob/master/EOGMADRIVE_LICENSE.md) and [LICENSE.md](https://github.com/ogmacorp/EOgmaDrive/blob/master/LICENSE.md) file for further information.

Contact Ogma via licenses@ogmacorp.com to discuss commercial use and licensing options.

EOgmaDrive Copyright (c) 2017 [Ogma Intelligent Systems Corp](https://ogmacorp.com). All rights reserved.
