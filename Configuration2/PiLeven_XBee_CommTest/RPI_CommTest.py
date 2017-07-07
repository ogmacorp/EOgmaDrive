# ----------------------------------------------------------------------------
#  EOgmaDrive
#  Copyright(c) 2017 Ogma Intelligent Systems Corp. All rights reserved.
#
#  This copy of EOgmaDrive is licensed to you under the terms described
#  in the EOGMADRIVE_LICENSE.md file included in this distribution.
# ----------------------------------------------------------------------------

# -*- coding: utf-8 -*-

#!/usr/bin/env python3
I2C_ADDR = 4
import smbus

bus = smbus.SMBus(1)

# 'a' should appear on the Pi-Top side (via Arduino IDE serial monitor)
bus.write_byte(I2C_ADDR, 97)
