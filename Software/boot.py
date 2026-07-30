# boot.py - Hardware USB Profile & Fingerprint Manager
# Executes BEFORE USB enumeration to the host PC
#
# NOTE: GP0 is read here via context manager (released after read).
# pins.py will reclaim GP0 for runtime use in code.py.

import board
import digitalio
import storage
import supervisor
import usb_cdc
import usb_midi
import usb_hid

_FW_VERSION = "2.1.0"
_SETUP_PIN = board.GP0


def _is_dev_mode_active():
    """Safely reads hardware jumper without locking GPIO resources."""
    try:
        with digitalio.DigitalInOut(_SETUP_PIN) as jumper:
            jumper.switch_to_input(pull=digitalio.Pull.UP)
            return not jumper.value
    except Exception:
        return False


def _configure_usb_profile():
    """Configure USB identity and peripheral visibility based on hardware mode."""
    # 1. Override hardware descriptors for stealth (BYOC model)
    #    VID 0x1209 = pid.codes open-source community
    #    PID 0x0001 = Generic HID keyboard
    supervisor.set_usb_identification(
        vid=0x1209,
        pid=0x0001,
        manufacturer="Generic",
        product="USB Keyboard"
    )

    if _is_dev_mode_active():
        print(f"[BOOT v{_FW_VERSION}] DEV MODE: Storage & Serial CDC enabled.")
        return

    # 2. Attack Mode: Minimize USB fingerprint to HID only
    print(f"[BOOT v{_FW_VERSION}] ATTACK MODE: Stealth generic HID profile active.")
    storage.disable_usb_drive()
    usb_cdc.disable()
    usb_midi.disable()

    # 3. Protect internal filesystem from corruption on unexpected power loss
    try:
        storage.remount("/", readonly=True)
    except RuntimeError:
        # May fail if filesystem is already in the desired state
        pass

    # 4. Configure HID interface — keyboard + consumer control + mouse
    usb_hid.enable(
        (usb_hid.Device.KEYBOARD, usb_hid.Device.CONSUMER_CONTROL, usb_hid.Device.MOUSE),
        boot_device=1
    )
    try:
        usb_hid.set_interface_name("USB Keyboard")
    except AttributeError:
        pass


_configure_usb_profile()