# USB Pico Ducky v2.1.0

High-Performance RP2040 DuckyScript Interpreter and Hardware HID Injection Platform

> [!WARNING]
> ### LEGAL DISCLAIMER AND TERMS OF USE
> This hardware device, firmware, and software suite are developed strictly for educational purposes, authorized laboratory environments, and professional security auditing.
>
> * **Authorized Use Only:** You must obtain explicit, written consent from the infrastructure or system owner before engaging in any security testing or payload injection.
> * **No Liability:** The creators and maintainers assume no liability and are not responsible for any damage, data loss, misuse, or illegal activities resulting from the deployment of this device.
> * **End-User Responsibility:** It is solely your responsibility to ensure compliance with all applicable local, state, and federal laws.

---

## Table of Contents / Tabla de Contenidos

- [English Documentation](#english-documentation)
- [Documentación en Español](#spanish-docs)

---

## English Documentation

### What Is USB Pico Ducky?

USB Pico Ducky is an open-source, hardware-based Human Interface Device (HID) injection platform powered by the RP2040 microcontroller and CircuitPython 10.x.

When plugged into any computer, it appears as a standard USB keyboard and mouse. The host operating system trusts it immediately — no drivers needed, no prompts, no warnings. The device then reads DuckyScript `.dd` files from a MicroSD card and types commands, moves the mouse, or presses key combinations exactly as if a real person were sitting at the keyboard.

Unlike basic keystroke injectors that require recompiling firmware for every script change, USB Pico Ducky works as a **dynamic execution engine**: swap the MicroSD card or flip a DIP switch, and you have a completely different payload ready to go — no reprogramming, no USB reflashing, no host software required.

#### Why Is It Different?

| Feature | Basic USB Injectors | USB Pico Ducky |
| :--- | :---: | :---: |
| Change scripts without reflashing | No | Yes (MicroSD) |
| Select payloads via hardware switch | No | Yes (4-bit DIP, 16 slots) |
| Variables, loops, conditionals | No | Yes (full scripting engine) |
| Mouse emulation | Rare | Yes (move, click, scroll, hold) |
| Human typing emulation (anti-EDR) | No | Yes (JITTER command) |
| Layout-independent typing | No | Yes (ALTSTRING / ALT-codes) |
| USB identity spoofing | No | Yes (custom VID/PID/name) |
| Multi-stage chained payloads | No | Yes (CHAIN command) |
| Reusable functions | No | Yes (FUNCTION / END_FUNCTION) |

---

### Hardware Compatibility

USB Pico Ducky supports two hardware configurations:

1. **Pico-USB Dedicated PCB:** Custom KiCad-designed board with dual-head USB connector (USB-A and USB-C on the same board edge), onboard SPI MicroSD slot, 4-position DIP switch for payload selection, and physical Dev Mode button on `GP0`.
2. **Standard Raspberry Pi Pico / RP2040 Boards:** Any off-the-shelf RP2040 development board. You only need to wire an external SPI MicroSD card module and a button on `GP0`. DIP switches are optional.

> [!IMPORTANT]
> **Dual-Head USB Safety:** The custom PCB's USB-A and USB-C connectors share the same internal data bus. Never connect both ports simultaneously to two different hosts or power sources.

---

### Installation and Setup Guide

#### Step 1 — Flash CircuitPython

1. Hold the **BOOTSEL** button on your RP2040 board while connecting the USB cable to your computer.
2. Release the button once the **RPI-RP2** drive appears in your file manager.
3. Download the official **CircuitPython 10.x** `.uf2` file for Raspberry Pi Pico from [circuitpython.org](https://circuitpython.org/).
4. Drag and drop the `.uf2` file into the `RPI-RP2` drive. The board reboots automatically and mounts a new drive called **CIRCUITPY**.

#### Step 2 — Copy Engine Files

Copy everything inside the `Software/` directory of this repository to the root of the **CIRCUITPY** drive:

```
CIRCUITPY/
  boot.py
  code.py
  duckyinpython.py
  pins.py
  settings.toml
  lib/
    adafruit_hid/
    adafruit_bus_device/
    adafruit_debouncer.mpy
    adafruit_sdcard.mpy
    adafruit_ticks.mpy
    asyncio/
```

> [!CAUTION]
> The `lib/` directory is mandatory. Without it, the device cannot emulate USB HID devices, read physical buttons, or access the MicroSD card.

#### Step 3 — Prepare Payloads on MicroSD

1. Format a MicroSD card as **FAT32**.
2. Copy your `.dd` payload scripts directly to the **root directory** of the card (for example: `payload.dd`, `payload1.dd`, `payload2.dd`).
3. Insert the MicroSD card into the device's SPI slot.

> [!NOTE]
> Payloads must be placed at the root of the MicroSD card, not inside subfolders. The engine looks for `/sd/payload.dd` (or `/sd/payload1.dd` through `/sd/payload15.dd` depending on the DIP switch position).

#### Step 4 — Understand the Two Operating Modes

Once the engine files are installed, the device has two modes controlled by the `GP0` pin:

| Mode | GP0 State | What Happens |
| :--- | :---: | :--- |
| **Attack Mode** (default) | Floating (not pressed) | CIRCUITPY drive is hidden. Serial console is disabled. Payload executes automatically on plug-in. The host sees only a generic USB keyboard and mouse. |
| **Development Mode** | Grounded (button held during plug-in) | CIRCUITPY drive is visible. Serial console is active. Payload does NOT auto-execute. Use this mode to edit files and debug. |

**To enter Development Mode:**
1. Press and hold the **DEV MODE** button (or bridge `GP0` to `GND` with a wire).
2. Plug in the USB cable while holding the button.
3. Release after plugging in. The CIRCUITPY drive and serial console will appear.

---

### USB Identity Spoofing and Configuration

This is a feature that most open-source HID injectors lack entirely. USB Pico Ducky **overrides the USB hardware descriptors before the host operating system ever sees the device**, making it appear as a completely generic keyboard.

The spoofing is configured in `boot.py` and takes effect at the hardware enumeration level — before any operating system driver loads:

| Descriptor | Default Value | Purpose |
| :--- | :--- | :--- |
| Vendor ID (VID) | `0x1209` | pid.codes open-source community VID |
| Product ID (PID) | `0x0001` | Generic HID device |
| Manufacturer String | `Generic` | Replaces "Raspberry Pi" / "Adafruit" |
| Product String | `USB Keyboard` | Replaces "Pico" / "CircuitPython" |

When plugged in Attack Mode, the host operating system enumerates only:
* A generic HID Keyboard
* A generic HID Mouse
* A Consumer Control device (for media keys)

No storage drives appear. No serial ports. No MIDI interfaces. No Raspberry Pi or Adafruit signatures in Device Manager, `lsusb`, or system logs.

> [!TIP]
> You can customize the VID, PID, manufacturer, and product strings by editing `boot.py`. This is useful for impersonating specific keyboard models to bypass device whitelists.

---

### Runtime Configuration (settings.toml)

The file `settings.toml` on the CIRCUITPY drive allows you to adjust engine behavior without modifying any Python code. Changes require a device reboot.

| Setting | Default | Description |
| :--- | :---: | :--- |
| `DEFAULT_DELAY_MS` | `0` | Global delay between commands in milliseconds |
| `PAYLOAD_EXTENSION` | `.dd` | File extension for payload scripts |
| `SD_MOUNT_TIMEOUT_SEC` | `2` | Seconds to wait for MicroSD filesystem readiness |
| `LOG_LEVEL` | `INFO` | Serial logging verbosity (`DEBUG`, `INFO`, `WARN`, `ERROR`) |
| `SD_POLL_INTERVAL_MS` | `100` | MicroSD polling interval in milliseconds |
| `WHILE_MAX_ITERATIONS` | `100000` | Safety limit for WHILE loops to prevent lockups |
| `SCROLL_WAIT_TIMEOUT_SEC` | `120` | Timeout for WAIT_FOR_SCROLL_CHANGE command |

---

### System Architecture

#### Asynchronous Execution Engine

The core engine (`code.py`) runs on `asyncio`, allowing three concurrent tasks to operate without blocking each other:

1. **Payload Execution** — Reads and executes the selected `.dd` script from MicroSD.
2. **LED Breathing Effect** — PWM-driven breathing animation on the onboard LED.
3. **LED State Monitor** — Watches host keyboard lock LEDs (Caps/Num/Scroll Lock) for data exfiltration protocols.

#### Resilience and Fallback Routing

The payload selector implements a 3-tier fallback strategy:
1. Attempts to load the DIP switch-selected payload (e.g., `/sd/payload3.dd`).
2. If not found, falls back to `/sd/payload.dd`.
3. If that is also missing, scans the MicroSD root for any `.dd` file.

**Kill-Switch:** If a file named `loot.bin` exists at the root of internal flash or the MicroSD card, all payload execution is aborted. This is a safety mechanism to prevent execution loops during data exfiltration testing.

#### GPIO Pin Mapping

| Peripheral | RP2040 Pin | Function | Logic |
| :--- | :---: | :--- | :--- |
| Dev Mode Switch | `GP0` | Development vs Attack Mode | Pull-Up (`GND = Dev`) |
| DIP Bit 0 (LSB) | `GP2` | Payload Selector | Active-Low |
| DIP Bit 1 | `GP3` | Payload Selector | Active-Low |
| DIP Bit 2 | `GP4` | Payload Selector | Active-Low |
| DIP Bit 3 (MSB) | `GP5` | Payload Selector | Active-Low |
| MicroSD MISO | `GP16` | SPI Data In | SPI0 |
| MicroSD CS | `GP17` | SPI Chip Select | Digital Out |
| MicroSD SCK | `GP18` | SPI Clock | SPI0 |
| MicroSD MOSI | `GP19` | SPI Data Out | SPI0 |

#### Payload Selector Truth Table (4-Bit DIP Switch)

| DIP State (3-2-1-0) | Decimal | Payload |
| :---: | :---: | :--- |
| `0000` | 0 | `/sd/payload.dd` |
| `0001` | 1 | `/sd/payload1.dd` |
| `0010` | 2 | `/sd/payload2.dd` |
| `0011` | 3 | `/sd/payload3.dd` |
| `0100` | 4 | `/sd/payload4.dd` |
| `0101` | 5 | `/sd/payload5.dd` |
| `0110` | 6 | `/sd/payload6.dd` |
| `0111` | 7 | `/sd/payload7.dd` |
| `1000` | 8 | `/sd/payload8.dd` |
| `1001` | 9 | `/sd/payload9.dd` |
| `1010` | 10 | `/sd/payload10.dd` |
| `1011` | 11 | `/sd/payload11.dd` |
| `1100` | 12 | `/sd/payload12.dd` |
| `1101` | 13 | `/sd/payload13.dd` |
| `1110` | 14 | `/sd/payload14.dd` |
| `1111` | 15 | `/sd/payload15.dd` |

---

### Complete DuckyScript v2.1 Command Reference

#### Typing and Keyboard

| Command | Description |
| :--- | :--- |
| `STRING <text>` | Types the given text |
| `STRINGLN <text>` | Types text and presses ENTER |
| `ALTSTRING <text>` | Types via Windows ALT+numpad codes (layout-independent) |
| `STRING` ... `END_STRING` | Multi-line text block (types all lines without ENTER) |
| `STRINGLN` ... `END_STRINGLN` | Multi-line text block (ENTER after each line) |
| `STRING_BLOCK` ... `END_STRING_BLOCK` | Explicit alias for multi-line STRING block |
| `STRINGLN_BLOCK` ... `END_STRINGLN_BLOCK` | Explicit alias for multi-line STRINGLN block |

#### Keys and Modifiers

Standard keys: `ENTER`, `SPACE`, `TAB`, `ESC`, `BACKSPACE`, `DELETE`, `INSERT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN`, `CAPSLOCK`, `NUMLOCK`, `SCROLLLOCK`, `PRINTSCREEN`, `PAUSE`

Arrow keys: `UP`, `DOWN`, `LEFT`, `RIGHT`

Modifier keys: `GUI` (Windows/Command), `SHIFT`, `CTRL`, `ALT`, `RSHIFT`, `RCTRL`, `RALT`, `RGUI`

Function keys: `F1` through `F24`

Application key: `APP` / `MENU`

Key combinations are written as space-separated tokens: `GUI r`, `CTRL SHIFT ESC`, `ALT F4`

| Command | Description |
| :--- | :--- |
| `HOLD <key>` | Presses and holds a key |
| `RELEASE <key>` | Releases a held key |
| `RESET` | Releases all held keys |
| `INJECT_MOD <combo>` | Strips prefix and executes remaining tokens as a key combo |

#### Mouse Emulation

| Command | Description |
| :--- | :--- |
| `MOUSE_MOVE <x> <y>` | Moves cursor relative to current position |
| `MOUSE_CLICK <LEFT\|RIGHT\|MIDDLE>` | Clicks specified button |
| `MOUSE_HOLD <button>` | Holds a mouse button |
| `MOUSE_RELEASE [button]` | Releases a button (or all if omitted) |
| `MOUSE_SCROLL <amount>` | Scrolls wheel (positive = up, negative = down) |

#### Timing and Evasion

| Command | Description |
| :--- | :--- |
| `DELAY <ms>` | Pauses execution for specified milliseconds |
| `DEFAULT_DELAY <ms>` | Sets global delay applied after every command |
| `JITTER <min_ms> <max_ms>` | Adds random delay per keystroke to mimic human typing |
| `JITTER OFF` | Disables jitter |
| `OVERCLOCK <mhz>` | Sets RP2040 CPU frequency (e.g., `200`) |
| `OVERCLOCK DEFAULT` | Reverts CPU to 125MHz |

#### Variables and Math

| Command | Description |
| :--- | :--- |
| `VAR $NAME = <expr>` | Declares a variable |
| `$NAME = <expr>` | Updates a variable |

Supported operators: `+`, `-`, `*`, `/`, `%` (modulo), `**` or `^` (power), `(`, `)`

Comparison operators: `==`, `!=`, `<`, `>`, `<=`, `>=`

Boolean operators: `&&` (AND), `||` (OR)

#### Control Flow

| Command | Description |
| :--- | :--- |
| `IF <condition>` | Begins conditional block |
| `ELSE IF <condition>` | Alternative condition |
| `ELSE` | Default branch |
| `END_IF` | Ends conditional block |
| `WHILE <condition>` | Begins loop (max 100,000 iterations by default) |
| `END_WHILE` | Ends loop |
| `FUNCTION <name>` | Defines a reusable block |
| `END_FUNCTION` | Ends function definition |
| `DEFINE <name> <value>` | Creates a text replacement macro |
| `REPEAT <n>` | Repeats the previous command `n` times |
| `CHAIN <file.dd>` | Transfers execution to another script on MicroSD |
| `IMPORT <file>` | Runs another script inline |
| `STOP_PAYLOAD` | Halts execution immediately |
| `RESTART_PAYLOAD` | Restarts the current script from the beginning |

#### Randomization

| Command | Description |
| :--- | :--- |
| `RANDOM_CHAR` | Types one random character (letter, digit, or symbol) |
| `RANDOM_NUMBER` | Types one random digit (0-9) |
| `RANDOM_LETTER` | Types one random letter (a-z or A-Z) |
| `RANDOM_LOWERCASE_LETTER` | Types one random lowercase letter (a-z) |
| `RANDOM_UPPERCASE_LETTER` | Types one random uppercase letter (A-Z) |
| `RANDOM_SPECIAL` | Types one random symbol |
| `$_RANDOM_INT` | Inserts a random integer within `$_RANDOM_MIN` to `$_RANDOM_MAX` range |
| `VID_RANDOM` | Types 4 random hex characters |
| `PID_RANDOM` | Types 4 random hex characters |
| `MAN_RANDOM` | Types 12 random alphanumeric characters |
| `PROD_RANDOM` | Types 12 random alphanumeric characters |
| `SERIAL_RANDOM` | Types 12 random mixed characters |

#### Media Keys (Consumer Control)

| Command | Description |
| :--- | :--- |
| `MK_VOLUP` | Volume Up |
| `MK_VOLDOWN` | Volume Down |
| `MK_MUTE` | Mute / Unmute |
| `MK_NEXT` | Next Track |
| `MK_PREV` | Previous Track |
| `MK_PP` | Play / Pause |
| `MK_STOP` | Stop |

#### LED and Hardware Control

| Command | Description |
| :--- | :--- |
| `LED` | Toggles onboard LED |
| `LED_OFF` | Turns LED off |
| `LED_G` | Turns LED on (green / full brightness) |
| `LED_R` | Turns LED on (red / full brightness) |

#### Host Keyboard State

| Command | Description |
| :--- | :--- |
| `SAVE_HOST_KEYBOARD_LOCK_STATE` | Saves current Caps/Num/Scroll Lock states |
| `RESTORE_HOST_KEYBOARD_LOCK_STATE` | Restores previously saved lock states |
| `WAIT_FOR_SCROLL_CHANGE` | Pauses until Scroll Lock toggles (or timeout) |

#### Comments and Debug

| Command | Description |
| :--- | :--- |
| `REM <text>` | Single-line comment (ignored by engine) |
| `REM_BLOCK` ... `END_REM` | Multi-line comment block |
| `PRINT <text>` | Outputs text to serial console (Dev Mode only) |

---

### DIY Wiring Guide (Standard Raspberry Pi Pico)

To build a working injector using a standard Raspberry Pi Pico:

1. **MicroSD Card Module (Required):** Wire a 3.3V SPI MicroSD breakout to SPI0:
   * MISO to `GP16`
   * CS to `GP17`
   * SCK to `GP18`
   * MOSI to `GP19`

2. **Dev Mode Button (Required):** Wire a momentary push button between `GP0` and `GND`. Without this, the Pico will always boot in Attack Mode and you will be locked out of the CIRCUITPY drive.

3. **DIP Switch (Optional):** Wire a 4-position DIP switch between `GND` and pins `GP2`, `GP3`, `GP4`, `GP5` for hardware payload selection. Without this, the device always runs `/sd/payload.dd`.

---

<a name="spanish-docs"></a>
## Documentación en Español

### Que es USB Pico Ducky?

USB Pico Ducky es una plataforma de inyeccion HID (Human Interface Device) de codigo abierto, basada en hardware, impulsada por el microcontrolador RP2040 y CircuitPython 10.x.

Cuando se conecta a cualquier computadora, aparece como un teclado y raton USB estandar. El sistema operativo del host lo acepta inmediatamente, sin necesidad de controladores, sin avisos y sin advertencias. El dispositivo entonces lee archivos DuckyScript `.dd` desde una tarjeta MicroSD y escribe comandos, mueve el raton o presiona combinaciones de teclas exactamente como si una persona real estuviera sentada frente al teclado.

A diferencia de los inyectores basicos que requieren recompilar el firmware para cada cambio de script, USB Pico Ducky funciona como un **motor de ejecucion dinamico**: intercambie la tarjeta MicroSD o mueva un interruptor DIP, y tendra un payload completamente diferente listo para ejecutarse, sin reprogramacion, sin reflasheo USB, sin software en el host.

#### Por que es diferente?

| Caracteristica | Inyectores USB Basicos | USB Pico Ducky |
| :--- | :---: | :---: |
| Cambiar scripts sin reflashear | No | Si (MicroSD) |
| Seleccionar payloads por hardware | No | Si (DIP 4 bits, 16 ranuras) |
| Variables, bucles, condicionales | No | Si (motor de scripting completo) |
| Emulacion de raton | Raro | Si (mover, clic, scroll, sostener) |
| Emulacion de escritura humana (anti-EDR) | No | Si (comando JITTER) |
| Escritura independiente del idioma del teclado | No | Si (ALTSTRING / codigos ALT) |
| Suplantacion de identidad USB | No | Si (VID/PID/nombre personalizados) |
| Payloads encadenados multi-etapa | No | Si (comando CHAIN) |
| Funciones reutilizables | No | Si (FUNCTION / END_FUNCTION) |

---

### Compatibilidad de Hardware

USB Pico Ducky soporta dos configuraciones de hardware:

1. **PCB Dedicada Pico-USB:** Placa personalizada diseñada en KiCad con conector USB dual (USB-A y USB-C en el mismo borde), ranura SPI MicroSD integrada, interruptor DIP de 4 posiciones y boton fisico de Modo Desarrollo en `GP0`.
2. **Raspberry Pi Pico / Placas RP2040 Estandar:** Cualquier placa de desarrollo RP2040 comercial. Solo necesita conectar un modulo SPI MicroSD externo y un boton en `GP0`. Los interruptores DIP son opcionales.

> [!IMPORTANT]
> **Seguridad del Conector Dual:** Los conectores USB-A y USB-C de la PCB personalizada comparten el mismo bus de datos interno. Nunca conecte ambos puertos simultaneamente a dos hosts o fuentes de alimentacion diferentes.

---

### Guia de Instalacion y Configuracion

#### Paso 1 — Grabar CircuitPython

1. Mantenga presionado el boton **BOOTSEL** en su placa RP2040 mientras conecta el cable USB a su computadora.
2. Suelte el boton cuando aparezca la unidad **RPI-RP2** en su explorador de archivos.
3. Descargue el archivo `.uf2` oficial de **CircuitPython 10.x** para Raspberry Pi Pico desde [circuitpython.org](https://circuitpython.org/).
4. Arrastre y suelte el archivo `.uf2` dentro de la unidad `RPI-RP2`. La placa se reiniciara automaticamente y montara una nueva unidad llamada **CIRCUITPY**.

#### Paso 2 — Copiar Archivos del Motor

Copie todo el contenido del directorio `Software/` de este repositorio a la raiz de la unidad **CIRCUITPY**:

```
CIRCUITPY/
  boot.py
  code.py
  duckyinpython.py
  pins.py
  settings.toml
  lib/
    adafruit_hid/
    adafruit_bus_device/
    adafruit_debouncer.mpy
    adafruit_sdcard.mpy
    adafruit_ticks.mpy
    asyncio/
```

> [!CAUTION]
> El directorio `lib/` es obligatorio. Sin el, el dispositivo no puede emular dispositivos USB HID, leer botones fisicos ni acceder a la tarjeta MicroSD.

#### Paso 3 — Preparar Payloads en MicroSD

1. Formatee una tarjeta MicroSD como **FAT32**.
2. Copie sus scripts de payload `.dd` directamente al **directorio raiz** de la tarjeta (por ejemplo: `payload.dd`, `payload1.dd`, `payload2.dd`).
3. Inserte la tarjeta MicroSD en la ranura SPI del dispositivo.

> [!NOTE]
> Los payloads deben estar en la raiz de la tarjeta MicroSD, no dentro de subcarpetas. El motor busca `/sd/payload.dd` (o `/sd/payload1.dd` a `/sd/payload15.dd` segun la posicion del interruptor DIP).

#### Paso 4 — Entender los Dos Modos de Operacion

Una vez instalados los archivos, el dispositivo tiene dos modos controlados por el pin `GP0`:

| Modo | Estado de GP0 | Que Sucede |
| :--- | :---: | :--- |
| **Modo Ataque** (predeterminado) | Flotante (no presionado) | La unidad CIRCUITPY se oculta. La consola serie se deshabilita. El payload se ejecuta automaticamente al conectar. El host solo ve un teclado y raton USB generico. |
| **Modo Desarrollo** | A tierra (boton presionado al conectar) | La unidad CIRCUITPY es visible. La consola serie esta activa. El payload NO se auto-ejecuta. Use este modo para editar archivos y depurar. |

**Para entrar en Modo Desarrollo:**
1. Presione y mantenga el boton **DEV MODE** (o conecte `GP0` a `GND` con un cable).
2. Conecte el cable USB mientras mantiene presionado el boton.
3. Suelte despues de conectar. La unidad CIRCUITPY y la consola serie apareceran.

---

### Suplantacion de Identidad USB y Configuracion

Esta es una caracteristica que la mayoria de los inyectores HID de codigo abierto no tienen. USB Pico Ducky **sobreescribe los descriptores USB del hardware antes de que el sistema operativo vea el dispositivo**, haciendolo aparecer como un teclado completamente generico.

La suplantacion se configura en `boot.py` y toma efecto a nivel de enumeracion de hardware, antes de que cualquier controlador del sistema operativo se cargue:

| Descriptor | Valor Predeterminado | Proposito |
| :--- | :--- | :--- |
| Vendor ID (VID) | `0x1209` | VID de la comunidad open-source pid.codes |
| Product ID (PID) | `0x0001` | Dispositivo HID generico |
| Cadena de Fabricante | `Generic` | Reemplaza "Raspberry Pi" / "Adafruit" |
| Cadena de Producto | `USB Keyboard` | Reemplaza "Pico" / "CircuitPython" |

Cuando se conecta en Modo Ataque, el sistema operativo del host solo enumera:
* Un teclado HID generico
* Un raton HID generico
* Un dispositivo de control de consumo (para teclas multimedia)

No aparecen unidades de almacenamiento. No hay puertos serie. No hay interfaces MIDI. No hay firmas de Raspberry Pi o Adafruit en el Administrador de Dispositivos, `lsusb` ni en los registros del sistema.

> [!TIP]
> Puede personalizar el VID, PID, fabricante y nombre del producto editando `boot.py`. Esto es util para hacerse pasar por modelos de teclado especificos y evadir listas blancas de dispositivos.

---

### Configuracion en Tiempo de Ejecucion (settings.toml)

El archivo `settings.toml` en la unidad CIRCUITPY permite ajustar el comportamiento del motor sin modificar codigo Python. Los cambios requieren reiniciar el dispositivo.

| Configuracion | Predeterminado | Descripcion |
| :--- | :---: | :--- |
| `DEFAULT_DELAY_MS` | `0` | Retardo global entre comandos en milisegundos |
| `PAYLOAD_EXTENSION` | `.dd` | Extension de archivo para scripts de payload |
| `SD_MOUNT_TIMEOUT_SEC` | `2` | Segundos de espera para la tarjeta MicroSD |
| `LOG_LEVEL` | `INFO` | Nivel de detalle de logs (`DEBUG`, `INFO`, `WARN`, `ERROR`) |
| `SD_POLL_INTERVAL_MS` | `100` | Intervalo de sondeo de la MicroSD en milisegundos |
| `WHILE_MAX_ITERATIONS` | `100000` | Limite de seguridad para bucles WHILE |
| `SCROLL_WAIT_TIMEOUT_SEC` | `120` | Timeout para el comando WAIT_FOR_SCROLL_CHANGE |

---

### Guia de Cableado DIY (Raspberry Pi Pico Estandar)

Para construir un inyector funcional usando una Raspberry Pi Pico estandar:

1. **Modulo MicroSD (Requerido):** Conecte un modulo SPI MicroSD de 3.3V al bus SPI0:
   * MISO a `GP16`
   * CS a `GP17`
   * SCK a `GP18`
   * MOSI a `GP19`

2. **Boton Modo Desarrollo (Requerido):** Conecte un boton pulsador momentaneo entre `GP0` y `GND`. Sin esto, la Pico siempre iniciara en Modo Ataque y quedara bloqueado fuera de la unidad CIRCUITPY.

3. **Interruptor DIP (Opcional):** Conecte un interruptor DIP de 4 posiciones entre `GND` y los pines `GP2`, `GP3`, `GP4`, `GP5` para seleccion de payload por hardware. Sin esto, el dispositivo siempre ejecuta `/sd/payload.dd`.

---

## Board Renders and Hardware Diagrams

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
