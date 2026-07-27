# pins.py - Hardware GPIO Configuration & Pin Mapping
# Standardized for RP2040 CircuitPython execution

import digitalio
from digitalio import DigitalInOut, Pull
import board
from board import *

# Setup/Configuration Jumper (GP0: GND = Dev Mode, Floating = Attack Mode)
progStatusPin = DigitalInOut(GP0)
progStatusPin.switch_to_input(pull=Pull.UP)

# Binary DIP Switch (CFG A6H-4101) - 4-bit decoding (0-15)
# Active-Low: Switch ON = GND (Bit 1), Switch OFF = Floating (Bit 0)
payload1Pin = DigitalInOut(GP2)
payload1Pin.switch_to_input(pull=Pull.UP)  # LSB (Bit 0)

payload2Pin = DigitalInOut(GP3)
payload2Pin.switch_to_input(pull=Pull.UP)  # Bit 1

payload3Pin = DigitalInOut(GP4)
payload3Pin.switch_to_input(pull=Pull.UP)  # Bit 2

payload4Pin = DigitalInOut(GP5)
payload4Pin.switch_to_input(pull=Pull.UP)  # MSB (Bit 3)