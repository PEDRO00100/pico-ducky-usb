> [!WARNING]
> ### ⚠️ LEGAL DISCLAIMER & TERMS OF USE
> 
> This hardware device, firmware, and its accompanying software suite are developed and provided **strictly for educational purposes, authorized laboratory environments, and professional security auditing.**
> 
> By building, accessing, or utilizing this tool, you acknowledge and agree to the following:
> 
> * **Authorized Use Only:** You must obtain explicit, written consent from the infrastructure or system owner before engaging in any security testing, payload injection, or assessment.
> * **No Liability:** The creators, contributors, and maintainers of this project assume **absolute no liability** and are not responsible for any direct or indirect damage, data loss, misuse, or illegal activities resulting from the deployment of this device.
> * **End-User Responsibility:** It is solely your responsibility to ensure compliance with all applicable local, state, and federal laws. Any use of this tool for malicious intent, unauthorized access, or covert data exfiltration is strictly prohibited.

## 💾 Firmware & Software Installation Guide

Setting up the device is divided into two straightforward phases: flashing the base interpreter (CircuitPython) and loading the attack engine. **This process is identical whether you are using our custom dedicated PCB or a generic Raspberry Pi Pico.**

### Step 1: Installing the Core Engine (CircuitPython)

To enable the RP2040 microcontroller to interpret attack scripts in real time, you must install the base CircuitPython firmware:

1. **Bootloader Mode:** Press and hold the onboard **`BOOTSEL`** physical button while plugging the USB cable into your computer.
2. **RPI-RP2 Drive:** Release the button once plugged in. Your operating system will automatically mount a mass storage drive named `RPI-RP2`.
3. **Flashing:** Download the latest official release of **CircuitPython 10.x** (`.uf2` file format) for the Raspberry Pi Pico / RP2040 and drag the file directly into the `RPI-RP2` drive.
4. **Automatic Reboot:** Once the copy completes, the drive will automatically eject, and the microcontroller will reboot, creating a new flash drive named **`CIRCUITPY`**.

---

### Step 2: Loading the Attack Engine & Dependencies

Once the `CIRCUITPY` drive is available, you must transfer the core operating logic and hardware libraries. Navigate to the `Software/` directory within this repository:

1. **Internal Flash (`CIRCUITPY` drive):**
   * Copy all core Python scripts (`boot.py`, `code.py`, `duckyinpython.py`, `pins.py`, `settings.toml`, and `LICENSE`) into the root of the `CIRCUITPY` drive.
   * **⚠️ CRITICAL - The `lib/` folder:** You **must** copy the entire **`lib/`** directory into the root of the `CIRCUITPY` drive. This folder contains essential drivers (`adafruit_hid`, `adafruit_debouncer`, etc.) required for keystroke injection and tactile button reading.

2. **External Storage (MicroSD Card):**
   * Inside this repository, there is an `sd/` folder. **This folder is merely symbolic** and serves as an example.
   * You must copy your `.dd` payload files **directly to the ROOT** of a FAT32-formatted MicroSD card. **Do NOT place them inside an `sd` folder on the card.**
   * Insert the MicroSD card into the onboard SPI slot. When the RP2040 boots, the system will automatically mount this physical card internally.

---

### Step 3: Access Management & Safe Mode (Critical!)

As soon as the system files are copied over, `boot.py` will take absolute control of the board's USB interfaces on every subsequent boot.

> 🚨 **AUTOMATIC INJECTION WARNING:**
> From this moment forward, **every time you plug the device into a USB port normally, it will boot in Attack Mode (Stealth Mode)**. This means the `CIRCUITPY` drive will completely disappear from your OS, and the payload on the MicroSD card **will execute automatically and immediately**.

#### 🛠️ How to re-access the `CIRCUITPY` drive to edit code?

To prevent the attack script from triggering and to mount the internal storage drive back onto your computer (e.g., to debug code or update core scripts), you must engage the hardware safety override:

1. **Press and hold the `DEV MODE` (`GP0`) button** on the board (or bridge `GP0` to `GND` on a standard Pico).
2. While holding the button down, **plug the USB cable** into your computer.
3. Once plugged in, you can safely release the button.
4. **Result:** The microcontroller detects the ground connection, aborts payload execution, and safely exposes the `CIRCUITPY` drive and Serial console.

---

## 📝 Supported DuckyScript Commands & Features

This firmware features a highly advanced DuckyScript parser, adding logic, evasion, and mouse emulation capabilities far beyond traditional injectors.

### ⌨️ Typing & Keyboard HID
* **`STRING <text>`**: Types the given string.
* **`STRINGLN <text>`**: Types the string and automatically presses ENTER.
* **`ALTSTRING <text>`**: Types characters using Windows ALT codes (e.g., ALT+065 for 'A'). This is incredibly useful for bypassing keyboard layout mismatches, as it injects specific characters regardless of the host machine's configured language settings.
* **`DELAY <ms>`**: Pauses execution for the specified milliseconds.
* **Standard Keys**: `ENTER`, `GUI` (Windows/Command key), `SHIFT`, `CTRL`, `ALT`, `TAB`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `ESC`, etc. (Can be combined, e.g., `GUI r` or `CTRL SHIFT ESC`).

### 🖱️ Mouse HID Emulation
Control the cursor without needing a physical mouse.
* **`MOUSE_MOVE <x> <y>`**: Moves the cursor relative to its current position (e.g., `MOUSE_MOVE 100 -50`).
* **`MOUSE_CLICK <LEFT|RIGHT|MIDDLE>`**: Clicks the specified button.
* **`MOUSE_HOLD <button>`** / **`MOUSE_RELEASE <button>`**: Holds or releases a mouse button for drag-and-drop actions.
* **`MOUSE_SCROLL <amount>`**: Scrolls the mouse wheel (positive for up, negative for down).

### ⏱️ Evasion & Performance
* **`JITTER <min_ms> <max_ms>`**: Adds a randomized delay between every single keystroke. This mimics human typing variance to evade Endpoint Detection and Response (EDR) and behavioral analysis tools that flag superhuman typing speeds. Use `JITTER OFF` to disable.
* **`OVERCLOCK <mhz>`**: Dynamically overclocks the RP2040 CPU for compute-heavy payloads (e.g., `OVERCLOCK 200`). Use `OVERCLOCK DEFAULT` to revert to 125MHz.

### 🔗 Logic & Execution Flow
* **`CHAIN <file.dd>`**: Immediately transfers execution to another payload file on the SD card, allowing modular, multi-stage attacks.
* **Variables & Math**: Declare using `VAR $NAME = 10`, update using `$NAME = $NAME + 5`.
* **Conditionals**: `IF $NAME == 15` / `ELSE` / `END_IF` blocks.
* **Loops**: `WHILE $COUNT < 5` / `END_WHILE` blocks.
* **Functions**: Define reusable blocks with `FUNCTION name` / `END_FUNCTION`, and call them by simply typing their name.
* **Randomization**: Insert random data on the fly using `RANDOM_NUMBER`, `RANDOM_CHAR`, `RANDOM_LOWERCASE_LETTER`, `RANDOM_SPECIAL`, etc.

---

## ⚙️ System Architecture & Hardware Specs

This project is a hardware-based security auditing and penetration testing tool (HID Injection Engine). Unlike traditional USB injection scripts that require hardcoding and recompiling firmware for every assessment, this device operates as an autonomous, dynamic execution engine.

### 1. Hardware & Peripheral Mapping

The PCB layout is engineered for signal integrity, prioritizing short trace lengths for high-speed SPI bus lines while keeping digital control switches isolated. The GPIO pin assignment on the RP2040 is structured as follows:

| Physical Peripheral | RP2040 Pin | System Function / Role | Electrical Logic |
| :--- | :---: | :--- | :--- |
| **Setup Mode Switch (`GP0/DEV`)** | `GP0` | Toggles between Development Mode & Attack Mode | Internal Pull-Up (`GND = Dev`) |
| **DIP Switch (Bit 0 - LSB)** | `GP2` | Binary Payload Selector (`payload1Pin` / `SWD-1`) | Active-Low (`GND = 1`) |
| **DIP Switch (Bit 1)** | `GP3` | Binary Payload Selector (`payload2Pin` / `SWD-2`) | Active-Low (`GND = 1`) |
| **DIP Switch (Bit 2)** | `GP4` | Binary Payload Selector (`payload3Pin` / `SWD-3`) | Active-Low (`GND = 1`) |
| **DIP Switch (Bit 3 - MSB)** | `GP5` | Binary Payload Selector (`payload4Pin` / `SWD-4`) | Active-Low (`GND = 1`) |
| **MicroSD SPI (MISO)** | `GP16` | Data receive from external storage | SPI0 Bus |
| **MicroSD SPI (CS)** | `GP17` | Chip Select / SD card activation | Digital Output |
| **MicroSD SPI (SCK)** | `GP18` | Bus clock synchronization | SPI0 Bus |
| **MicroSD SPI (MOSI)** | `GP19` | Data transmit to external storage | SPI0 Bus |

#### 🔌 Dual-Head USB Interface & Protection
The hardware features a versatile **Dual-Head USB architecture**, integrating both **USB-A** and **USB-C** connectors directly onto the PCB edge. 
* **⚠️ Critical Safety Rule:** The dual connectors share the same internal USB data bus. **Never connect both USB-A and USB-C ports simultaneously to two different host devices or power sources**, as this could cause bus contention or electrical back-feeding.

---

### 2. Binary Payload Selector (4-Bit DIP Switch)

To eliminate the need for reprogramming the device between different engagement scenarios, the board features an onboard 4-position DIP switch (`A6H-4101`) operating on **pure binary decoding**.

```text
Bit 3 (MSB)   Bit 2       Bit 1       Bit 0 (LSB)
  [GP5]       [GP4]       [GP3]       [GP2]
  Value: 8    Value: 4    Value: 2    Value: 1
```

* **Combination `0000` (All OFF):** Executes the default script located at `/sd/payload.dd`.
* **Combinations `0001` through `1111` (1 to 15):** Sums the active bit values in powers of 2 and dynamically routes execution to the numbered script on the MicroSD card (from `/sd/payload1.dd` up to `/sd/payload15.dd`).

---

### 3. Operating Modes & USB Stealth Spoofing

#### 🔴 Attack / Stealth Mode (`GP0` floating / Unpressed)
* **Purpose:** Active field auditing and Endpoint Detection & Response (EDR / DLP) evasion.
* **USB Profile:** The firmware executes `storage.disable_usb_drive()`, completely hiding internal Flash memory from the host OS and disabling Serial/MIDI endpoints.
* **Identity Spoofing:** To prevent triggering vendor-specific blocklists while adhering to safe open-source distribution standards, the device overrides its hardware descriptors using the open community VID **`0x1209`** (pid.codes) and generic keyboard PID **`0x0001`**.

> ⚠️ **Tactical Advantage:** When plugged into a host system in Attack Mode, the operating system **strictly enumerates a generic HID USB Keyboard & Mouse**. No storage drives are mounted, no COM ports appear in Device Manager, and no Raspberry Pi / Adafruit hardware signatures are exposed.

---

### 4. Asynchronous Execution Engine & Resilience

The core execution engine (`code.py`) is built around asynchronous event loops (`asyncio`). This allows the microcontroller to handle concurrent background tasks—such as button debouncing, filesystem polling, and monitoring host keyboard lock LEDs—without causing latency or blocking keystroke injection.

To guarantee field reliability and prevent kernel panics during live deployments, the firmware implements multiple defensive architecture layers:

1. **Zero-RAM Lazy Reading:** Payload execution consumes a flat `O(1)` memory footprint, streaming directly from the MicroSD card to prevent `MemoryError` crashes on massive payloads.
2. **3-Tier Fallback Routing:** If an indexed script cannot be read, the execution pipeline gracefully degrades to a standard `payload.dd`, and finally to any `.dd` file present, ensuring the assessment does not fail silently.
3. **Hardware Kill-Switch:** If the engine detects a file named `loot.bin` in the root directory, it aborts exfiltration overrides to prevent execution loops.

---

## 🛠️ DIY Protoboard Build (Standard Raspberry Pi Pico)

If you are prototyping on a breadboard or building a custom DIY injection tool using an original Raspberry Pi Pico, you can deploy this firmware without modifying a single line of code. You simply need to manually wire the external modules according to the hardware mapping defined in `pins.py`:

### 📌 DIY Wiring Checklist:
* **MicroSD Card Module:** Wire a 3.3V SPI MicroSD breakout board directly to the RP2040's **SPI0 bus** (`MISO` -> `GP16`, `CS` -> `GP17`, `SCK` -> `GP18`, and `MOSI` -> `GP19`).
* **4-Bit Binary DIP Switch:** Connect four mechanical switches (or simple jumper wires) between ground (`GND`) and pins **`GP2`**, **`GP3`**, **`GP4`**, and **`GP5`**. When closed (grounded), the internal pull-up resistor drops to `0V`, which the software decodes as an active binary `1`.
* **Development Mode Safety Jumper (`GP0`):** You **must** wire a tactile button or jumper wire between **`GP0`** and **`GND`**. This is critical: without this physical override, an off-the-shelf Pico will permanently boot in Stealth Attack Mode, hiding the USB drive and locking you out of the REPL console.

---

## 📸 Board Designs & Renders

3D renders and PCB layer routing for the **Pico-USB** board.

<table align="center">
  <tr>
    <td align="center">
      <img src="assets/3dFront.png" alt="3D Front View" height="320"/><br/>
      <sub><b>3D Front</b></sub>
    </td>
    <td align="center">
      <img src="assets/3dBack.png" alt="3D Back View" height="320"/><br/>
      <sub><b>3D Back</b></sub>
    </td>
    <td align="center">
      <img src="assets/2dFront.png" alt="2D Front Routing (F.Cu)" height="320"/><br/>
      <sub><b>2D F.Cu</b></sub>
    </td>
    <td align="center">
      <img src="assets/2dBack.png" alt="2D Back Routing (B.Cu)" height="320"/><br/>
      <sub><b>2D B.Cu</b></sub>
    </td>
  </tr>
</table>
