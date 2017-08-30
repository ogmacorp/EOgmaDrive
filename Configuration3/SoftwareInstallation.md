<!---
  EOgmaDrive
  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.

  This copy of EOgmaDrive is licensed to you under the terms described
  in the EOGMADRIVE_LICENSE.md file included in this distribution.
--->

# Configuration3 (uSDC)

[![Join the chat at https://gitter.im/ogmaneo/Lobby](https://img.shields.io/gitter/room/nwjs/nw.js.svg)](https://gitter.im/ogmaneo/Lobby)

## Software setup

Once the assembly instructions ([AssemblyInstructions.md](AssemblyInstructions.md)) have been finished the Raspberry Pi ZeroW can be setup with the appropriate software.

### Jessie image setup

Prepare the Raspberry Pi ZeroW for access via the command line:

- Download [Raspbian Jessie image](https://www.raspberrypi.org/downloads/raspbian/).
- Flash the image to a micro SD card.
- Edit the config.txt and configure.txt boot files, and create the empty `ssh` file. To allow for SSH over USB (e.g. https://gist.github.com/gbaman/975e2db164b3ca2b51ae11e45e8fd40a).
- Configure WiFi (e.g. https://raspberrypi.stackexchange.com/questions/62933/set-up-a-raspberry-pi-zero-w-without-monitor-or-ethernet-module?noredirect=1&lq=1).

### Create a SSH shell into the Pi Zero

- Connect the Raspberry Pi ZeroW `usb` port (not the `pwr`) to a PC/laptop using a USB data cable.
- Use `ssh pi@raspberrypi.local` (or `ssh pi@raspberrypi` if configured to use WiFi). Alternatively use PuTTY, for example, to create a SSH shell into the device.

### Update Jessie

On the Pi ZeroW, use the following commands to configure and update it:

- Run `sudo raspi-config` to configure the Pi Zero. Options to change:
  - `5 Interfacing Options` -> `P1 Camera` to enable the Camera interface.
  - `7 Advanced Options` -> `A1 Expand Filesystem` to make sure it uses all of your SD card.
- Run `sudo apt update` followed by `sudo apt upgrade`, to make sure all packages are up to date.
- Use `sudo shutdown -h now` to power off the device.

### Install support packages

#### Common dependencies

```bash
sudo apt-get install cmake git python-dev python3-dev
```

#### Explorer pHAT

The easiest way is using the following command:
```
curl https://get.pimoroni.com/explorerhat | bash
```

Choose `y` (yes) for **all** questions asked by this bash script. The script will initial make sure that your Jessie image contains all the required packages (e.g. Python & Pip, Python3 & Pip3, and the I2C hardware interface is enabled).

Choosing `y` (yes) to the full install questions installs all the necessary Python(3) packages/dependencies required by the Explorer pHAT, its examples and documentation. Dependencies include packages such as PyGame, Git, SMBus, Cap1xxx, and ExplorerHat.

Upon completion of the bash script it should print "All Done. ...". At this point it is possible to check the motor connections using:

```python
$ python
>>> import explorerhat
Explorer pHAT detected...
>>> explorerhat.help()
...
>>> explorerhat.help("motor")
...
>>> explorerhat.motor.one.speed(10)
10
>>> explorerhat.motor.one.speed(0)
0
>>> explorerhat.motor.two.speed(10)
10
>>> explorerhat.motor.two.speed(0)
0
>>> exit()
```

Full installation instructions can be found here - https://github.com/pimoroni/explorer-hat

#### Camera Python module

Installation of the Python packages can be done using:

```bash
sudo apt-get install python-picamera python3-picamera
```

The following "Basic Recipe" (http://picamera.readthedocs.io/en/release-1.13/recipes1.html) can be used to capture an image using the SainSmart camera:

```python
$ cd ~
$ python
>>> from time import sleep
>>> from picamera import PiCamera
>>> camera = PiCamera()
>>> camera.resolution = (1024, 768)
>>> camera.start_preview()
>>> sleep(2)
>>> camera.capture('foo.jpg')
>>> exit()
```

From a host computer the following command can be used to obtain the image:
> scp pi@raspberrypi:/home/pi/foo.jpg ./foo.jpg

Further information about this Python interface can be found here: http://picamera.readthedocs.io/en/release-1.13/

#### Steam Controller

Stany Marcel's `Standalone Steam Controller Driver` is used to obtain control information from the controller using Python. It can be found on Github here: https://github.com/ynsta/steamcontroller

The following is a copy of the installation instructions:

```bash
cd ~
sudo pip3 install libusb1
sudo pip install libusb1
sudo pip install enum34
git clone https://github.com/ynsta/steamcontroller.git
cd steamcontroller
sudo python3 setup.py install
```

Create the following udev rules in a new file called `/etc/udev/rules.d/99-steam-controller.rules`

```text
# Steam controller keyboard/mouse mode
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", GROUP="games", MODE="0660"

# Steam controller gamepad mode
KERNEL=="uinput", MODE="0660", GROUP="games", OPTIONS+="static_node=uinput"
```

Reload udev with:

```bash
sudo udevadm control --reload
sudo reboot
```

After the reboot, restart a SSH shell and use the following to make sure that the Steam controller and USB dongle are working:

```bash
cd ~
sudo python3 ~/steamcontroller/scripts/sc-dump.py
```

#### OpenCV with Python bindings

Building OpenCV fresh from source code can take ~9 hours on the Raspberry Pi ZeroW. Therefore, the recommended way is to use a pre-built package.

Jaimyn Mayer supplies a package for OpenCV 3.1.0 on Github. Installation instructions can be found here: https://github.com/jabelone/OpenCV-for-Pi

#### SWIG

This needs to be installed to allow for the creation of Python bindings for EOgmaNeo. The following can be used to install this required package:

```bash
sudo apt-get install swig3.0
```

#### EOgmaNeo library

The following commands can be used to install the EOgmaNeo library:

```bash
cd ~
git clone https://github.com/ogmacorp/EOgmaNeo.git
cd EOgmaNeo/Python
sudo python3 setup.py install
```

#### EOgmaDrive

Clone the EOgmaDrive repository, or a fork of the repo:

```bash
cd ~
git clone https://github.com/ogmacorp/EOgmaDrive.git
cd EOgmaDrive/Configuration3
```

### Setup complete

All the required packages and dependencies have now been setup, and EOgmaDrive is ready to be tested. Head back to the main [Readme.md](Readme.md) file for further details.

## License and Copyright

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />The work in this repository is licensed under the <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>. See the  [EOGMADRIVE_LICENSE.md](https://github.com/ogmacorp/EOgmaDrive/blob/master/EOGMADRIVE_LICENSE.md) and [LICENSE.md](https://github.com/ogmacorp/EOgmaDrive/blob/master/LICENSE.md) file for further information.

Contact Ogma via licenses@ogmacorp.com to discuss commercial use and licensing options.

EOgmaDrive Copyright (c) 2017 [Ogma Intelligent Systems Corp](https://ogmacorp.com). All rights reserved.
