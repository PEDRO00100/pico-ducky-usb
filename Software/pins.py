# pins.py - Hardware GPIO Configuration & Pin Mapping
# Standardized for RP2040 CircuitPython execution
#
# Physical Pin Layout (Active-Low with internal pull-ups):
# ┌─────────────────────────────────────────────────┐
# │  GP0  → DEV Mode Switch  (GND = Dev Mode)       │
# │  GP2  → DIP Switch Bit 0 (LSB, GND = Active)    │
# │  GP3  → DIP Switch Bit 1 (GND = Active)         │
# │  GP4  → DIP Switch Bit 2 (GND = Active)         │
# │  GP5  → DIP Switch Bit 3 (MSB, GND = Active)    │
# │  GP16 → SD Card MISO  (SPI0)                    │
# │  GP17 → SD Card CS    (SPI0)                    │
# │  GP18 → SD Card SCK   (SPI0)                    │
# │  GP19 → SD Card MOSI  (SPI0)                    │
# └─────────────────────────────────────────────────┘
#
# NOTE: GP0 is first configured in boot.py using a context manager
# (which releases it after reading). This module then reclaims it
# for runtime use by code.py / duckyinpython.py.

import digitalio
from digitalio import DigitalInOut, Pull
from board import GP0, GP2, GP3, GP4, GP5

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