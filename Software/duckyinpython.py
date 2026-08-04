# License: GPLv2.0
# Copyright (c) 2026 Dave Bailey (dbisu, @daveisu)
# Modified by: Pedro Pacheco, Nahum Silvestre Martinez
# RP2040 hardware adaptation and system modifications.

import gc
import os
import re
import time
import random
import board
import asyncio
import usb_hid
import microcontroller
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
from pins import progStatusPin, payload1Pin, payload2Pin, payload3Pin, payload4Pin

# US keyboard layout (swap for non-US layouts)
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout
from adafruit_hid.keycode import Keycode

# HID devices
kbd = Keyboard(usb_hid.devices)
consumerControl = ConsumerControl(usb_hid.devices)
layout = KeyboardLayout(kbd)
try:
    mouse = Mouse(usb_hid.devices)
except Exception:
    mouse = None

defaultDelay = 0
_DEV_MODE = not progStatusPin.value


def _log(msg):
    """Debug output. Silent when CDC is disabled (attack mode)."""
    if _DEV_MODE:
        print(msg)


# Jitter (anti-behavioral detection)
_jitter_min_ms = 0
_jitter_max_ms = 0

_MOUSE_BUTTONS = {
    'LEFT': Mouse.LEFT_BUTTON,
    'RIGHT': Mouse.RIGHT_BUTTON,
    'MIDDLE': Mouse.MIDDLE_BUTTON,
} if mouse else {}


# LED state helpers
def _capsOn():
    return kbd.led_on(Keyboard.LED_CAPS_LOCK)

def _numOn():
    return kbd.led_on(Keyboard.LED_NUM_LOCK)

def _scrollOn():
    return kbd.led_on(Keyboard.LED_SCROLL_LOCK)

def _press_lock(key):
    kbd.press(key)
    kbd.release(key)

def _save_keyboard_led_state():
    variables["$_INITIAL_SCROLLLOCK"] = _scrollOn()
    variables["$_INITIAL_NUMLOCK"] = _numOn()
    variables["$_INITIAL_CAPSLOCK"] = _capsOn()

def _restore_keyboard_led_state():
    if variables["$_INITIAL_CAPSLOCK"] != _capsOn():
        _press_lock(Keycode.CAPS_LOCK)
    if variables["$_INITIAL_NUMLOCK"] != _numOn():
        _press_lock(Keycode.NUM_LOCK)
    if variables["$_INITIAL_SCROLLLOCK"] != _scrollOn():
        _press_lock(Keycode.SCROLL_LOCK)


# Keycode maps
duckyKeys = {
    'WINDOWS': Keycode.GUI, 'RWINDOWS': Keycode.RIGHT_GUI,
    'GUI': Keycode.GUI, 'RGUI': Keycode.RIGHT_GUI,
    'COMMAND': Keycode.GUI, 'RCOMMAND': Keycode.RIGHT_GUI,
    'APP': Keycode.APPLICATION, 'MENU': Keycode.APPLICATION,
    'SHIFT': Keycode.SHIFT, 'RSHIFT': Keycode.RIGHT_SHIFT,
    'ALT': Keycode.ALT, 'RALT': Keycode.RIGHT_ALT,
    'OPTION': Keycode.ALT, 'ROPTION': Keycode.RIGHT_ALT,
    'CONTROL': Keycode.CONTROL, 'CTRL': Keycode.CONTROL,
    'RCTRL': Keycode.RIGHT_CONTROL,
    'DOWNARROW': Keycode.DOWN_ARROW, 'DOWN': Keycode.DOWN_ARROW,
    'LEFTARROW': Keycode.LEFT_ARROW, 'LEFT': Keycode.LEFT_ARROW,
    'RIGHTARROW': Keycode.RIGHT_ARROW, 'RIGHT': Keycode.RIGHT_ARROW,
    'UPARROW': Keycode.UP_ARROW, 'UP': Keycode.UP_ARROW,
    'BREAK': Keycode.PAUSE, 'PAUSE': Keycode.PAUSE,
    'CAPSLOCK': Keycode.CAPS_LOCK, 'DELETE': Keycode.DELETE,
    'END': Keycode.END, 'ESC': Keycode.ESCAPE, 'ESCAPE': Keycode.ESCAPE,
    'HOME': Keycode.HOME, 'INSERT': Keycode.INSERT,
    'NUMLOCK': Keycode.KEYPAD_NUMLOCK,
    'PAGEUP': Keycode.PAGE_UP, 'PAGEDOWN': Keycode.PAGE_DOWN,
    'PRINTSCREEN': Keycode.PRINT_SCREEN, 'ENTER': Keycode.ENTER,
    'SCROLLLOCK': Keycode.SCROLL_LOCK, 'SPACE': Keycode.SPACE,
    'TAB': Keycode.TAB, 'BACKSPACE': Keycode.BACKSPACE,
    'A': Keycode.A, 'B': Keycode.B, 'C': Keycode.C, 'D': Keycode.D,
    'E': Keycode.E, 'F': Keycode.F, 'G': Keycode.G, 'H': Keycode.H,
    'I': Keycode.I, 'J': Keycode.J, 'K': Keycode.K, 'L': Keycode.L,
    'M': Keycode.M, 'N': Keycode.N, 'O': Keycode.O, 'P': Keycode.P,
    'Q': Keycode.Q, 'R': Keycode.R, 'S': Keycode.S, 'T': Keycode.T,
    'U': Keycode.U, 'V': Keycode.V, 'W': Keycode.W, 'X': Keycode.X,
    'Y': Keycode.Y, 'Z': Keycode.Z,
    'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3,
    'F4': Keycode.F4, 'F5': Keycode.F5, 'F6': Keycode.F6,
    'F7': Keycode.F7, 'F8': Keycode.F8, 'F9': Keycode.F9,
    'F10': Keycode.F10, 'F11': Keycode.F11, 'F12': Keycode.F12,
    'F13': Keycode.F13, 'F14': Keycode.F14, 'F15': Keycode.F15,
    'F16': Keycode.F16, 'F17': Keycode.F17, 'F18': Keycode.F18,
    'F19': Keycode.F19, 'F20': Keycode.F20, 'F21': Keycode.F21,
    'F22': Keycode.F22, 'F23': Keycode.F23, 'F24': Keycode.F24,
}

duckyConsumerKeys = {
    'MK_VOLUP': ConsumerControlCode.VOLUME_INCREMENT,
    'MK_VOLDOWN': ConsumerControlCode.VOLUME_DECREMENT,
    'MK_MUTE': ConsumerControlCode.MUTE,
    'MK_NEXT': ConsumerControlCode.SCAN_NEXT_TRACK,
    'MK_PREV': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
    'MK_PP': ConsumerControlCode.PLAY_PAUSE,
    'MK_STOP': ConsumerControlCode.STOP,
}


# Runtime state
variables = {
    "$_RANDOM_MIN": 0,
    "$_RANDOM_MAX": 65535,
    "$_EXFIL_MODE_ENABLED": False,
    "$_EXFIL_LEDS_ENABLED": False,
    "$_INITIAL_SCROLLLOCK": False,
    "$_INITIAL_NUMLOCK": False,
    "$_INITIAL_CAPSLOCK": False,
}

internalVariables = {
    "$_CAPSLOCK_ON": _capsOn,
    "$_NUMLOCK_ON": _numOn,
    "$_SCROLLLOCK_ON": _scrollOn,
}
# Pre-sorted once (never changes) to avoid sorting every replaceVariables call
_INTERNAL_VAR_KEYS = sorted(internalVariables.keys(), key=len, reverse=True)

defines = {}
functions = {}

# Pre-allocated character sets
LETTERS = "abcdefghijklmnopqrstuvwxyz"
LETTERS_UPPER = LETTERS.upper()
NUMBERS = "0123456789"
SPECIAL_CHARS = "!@#$%^&*()"
ALL_CHARS = LETTERS + LETTERS_UPPER + NUMBERS + SPECIAL_CHARS
HEX_CHARS = NUMBERS + "ABCDEF"
ALPHANUM_CHARS = LETTERS + LETTERS_UPPER + NUMBERS

# Pre-compiled regex (avoids re-parsing patterns per call)
_RE_VAR_DECL = re.compile(r"VAR\s+\$(\w+)\s*=\s*(.+)")
_RE_VAR_UPDATE = re.compile(r"\$(\w+)\s*=\s*(.+)")
_RE_TRUE = re.compile(r'[Tt][Rr][Uu][Ee]')
_RE_FALSE = re.compile(r'[Ff][Aa][Ll][Ss][Ee]')

# Safety limits
_WHILE_MAX_ITERATIONS = 100_000
_SCROLL_WAIT_TIMEOUT_SEC = 120
_EXFIL_TIMEOUT_SEC = 3600

# Numpad ALT-code keymap
_NUMPAD_MAP = {
    '0': Keycode.KEYPAD_ZERO, '1': Keycode.KEYPAD_ONE,
    '2': Keycode.KEYPAD_TWO, '3': Keycode.KEYPAD_THREE,
    '4': Keycode.KEYPAD_FOUR, '5': Keycode.KEYPAD_FIVE,
    '6': Keycode.KEYPAD_SIX, '7': Keycode.KEYPAD_SEVEN,
    '8': Keycode.KEYPAD_EIGHT, '9': Keycode.KEYPAD_NINE,
}

# LED reference (injected by code.py)
_led_ref = None

def _set_led_ref(led_obj):
    global _led_ref
    _led_ref = led_obj

# Pre-computed LED breathing duty cycles (avoids 16x int(i*655.35) per cycle)
_LED_FADE_UP = (0, 9174, 18396, 27524, 37354, 46529, 55704, 65535)
_LED_FADE_DOWN = (65535, 55704, 46529, 37354, 27524, 18396, 9174, 0)


# IF/ELSE/END_IF block handler
class IF:
    def __init__(self, condition, lines_iter):
        self.condition = condition
        self.lines_iter = lines_iter
        self.lastIfResult = None

    def _exitIf(self):
        depth = 0
        safety = 0
        while True:
            line = _safe_next(self.lines_iter)
            if line is None:
                break
            safety += 1
            if safety > _WHILE_MAX_ITERATIONS:
                _log("[WARN] _exitIf safety limit reached.")
                break
            line = line.strip()
            upper = line.upper()
            if upper.startswith("END_IF"):
                depth -= 1
            elif upper.startswith("IF"):
                depth += 1
            if depth < 0:
                break
        return self.lines_iter

    async def runIf(self):
        if isinstance(self.condition, str):
            self.lastIfResult = evaluateExpression(self.condition)
        elif isinstance(self.condition, bool):
            self.lastIfResult = self.condition
        else:
            raise ValueError("Invalid condition type")

        depth = 0
        safety = 0
        while True:
            line = _safe_next(self.lines_iter)
            if line is None:
                return (self.lines_iter, self.lastIfResult)
            safety += 1
            if safety > _WHILE_MAX_ITERATIONS:
                _log("[WARN] IF block safety limit reached.")
                return (self.lines_iter, self.lastIfResult)
            line = line.strip()
            if not line:
                continue

            if line.startswith("IF"):
                depth += 1
            elif line.startswith("END_IF"):
                if depth == 0:
                    return (self.lines_iter, -1)
                depth -= 1
            elif line.startswith("ELSE") and depth == 0:
                if self.lastIfResult is False:
                    line = line[4:].strip()
                    if line.startswith("IF"):
                        nested = _getIfCondition(line)
                        self.lines_iter, self.lastIfResult = await IF(
                            nested, self.lines_iter
                        ).runIf()
                        if self.lastIfResult == -1 or self.lastIfResult is True:
                            return (self.lines_iter, True)
                    else:
                        return await IF(True, self.lines_iter).runIf()
                else:
                    self.lines_iter = self._exitIf()
                    break
            elif self.lastIfResult:
                self.lines_iter = await parseLine(line, self.lines_iter)

        return (self.lines_iter, self.lastIfResult)


def _getIfCondition(line):
    cond = str(line).strip()
    if cond.upper().startswith("IF "):
        cond = cond[3:].strip()
    if cond.upper().endswith(" THEN"):
        cond = cond[:-5].strip()
    return cond


def _isCodeBlock(line):
    u = line.strip().upper()
    return u.startswith("IF") or u.startswith("WHILE")


def _getCodeBlock(lines_iter):
    """Collect loop body until matching END_ marker. Preserves trailing whitespace."""
    code = []
    depth = 1
    while True:
        line = _safe_next(lines_iter)
        if line is None:
            break
        line = line.rstrip("\r\n").lstrip(" \t")
        check = line.strip().upper()
        if check.startswith("END_"):
            depth -= 1
        elif _isCodeBlock(line):
            depth += 1
        if depth <= 0:
            break
        code.append(line)
    return code


# Expression evaluator (recursive descent parser)
def evaluateExpression(expression):
    """Safely evaluate a DuckyScript math/logic expression."""
    expression = replaceVariables(expression)
    expression = _RE_TRUE.sub('True', expression)
    expression = _RE_FALSE.sub('False', expression)
    expression = expression.replace("&&", " and ").replace("||", " or ")
    tokens = _tokenize(expression)
    pos = [0]

    def _peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def _advance():
        tok = tokens[pos[0]]
        pos[0] += 1
        return tok

    def _parse_or():
        left = _parse_and()
        while _peek() == 'or':
            _advance()
            left = left or _parse_and()
        return left

    def _parse_and():
        left = _parse_not()
        while _peek() == 'and':
            _advance()
            left = left and _parse_not()
        return left

    def _parse_not():
        tok = _peek()
        if tok == 'not' or tok == '!':
            _advance()
            return not _parse_not()
        return _parse_comparison()

    def _parse_comparison():
        left = _parse_add()
        while _peek() in ('==', '!=', '<', '>', '<=', '>='):
            op = _advance()
            right = _parse_add()
            if op == '==':
                left = left == right
            elif op == '!=':
                left = left != right
            elif op == '<':
                left = left < right
            elif op == '>':
                left = left > right
            elif op == '<=':
                left = left <= right
            elif op == '>=':
                left = left >= right
        return left

    def _parse_add():
        left = _parse_mul()
        while _peek() in ('+', '-'):
            op = _advance()
            right = _parse_mul()
            left = left + right if op == '+' else left - right
        return left

    def _parse_mul():
        left = _parse_power()
        while _peek() in ('*', '/', '%'):
            op = _advance()
            right = _parse_power()
            if op == '*':
                left = left * right
            elif op == '/':
                left = left / right
            else:
                left = left % right
        return left

    def _parse_power():
        left = _parse_unary()
        tok = _peek()
        if tok == '**' or tok == '^':
            _advance()
            left = left ** _parse_power()
        return left

    def _parse_unary():
        if _peek() == '-':
            _advance()
            return -_parse_unary()
        if _peek() == '+':
            _advance()
            return _parse_unary()
        return _parse_primary()

    def _parse_primary():
        tok = _peek()
        if tok == '(':
            _advance()
            val = _parse_or()
            if _peek() == ')':
                _advance()
            return val
        _advance()
        if tok == 'True':
            return True
        if tok == 'False':
            return False
        try:
            return int(tok)
        except (ValueError, TypeError):
            pass
        try:
            return float(tok)
        except (ValueError, TypeError):
            pass
        return tok

    return _parse_or()


def _tokenize(expr):
    """Split expression string into operator and operand tokens."""
    tokens = []
    i = 0
    s = expr.strip()
    n = len(s)
    while i < n:
        c = s[i]
        if c == ' ' or c == '\t':
            i += 1
            continue
        if i + 1 < n:
            two = s[i:i+2]
            if two in ('==', '!=', '<=', '>=', '**'):
                tokens.append(two)
                i += 2
                continue
        if c in '+-*/%^()!':
            tokens.append(c)
            i += 1
            continue
        j = i
        while j < n and s[j] not in ' \t+-*/%^()!=<>':
            j += 1
        if j > i:
            tokens.append(s[i:j])
            i = j
            continue
        if c in '<>':
            tokens.append(c)
            i += 1
            continue
        i += 1
    return tokens


# Key conversion and string injection
def convertLine(line):
    """Convert a DuckyScript key combo line into a list of keycodes."""
    commands = []
    for key in filter(None, line.split(" ")):
        key = key.upper()
        kc = duckyKeys.get(key)
        if kc is not None:
            commands.append(kc)
        else:
            ckc = duckyConsumerKeys.get(key)
            if ckc is not None:
                commands.append(1000 + ckc)
            elif hasattr(Keycode, key):
                commands.append(getattr(Keycode, key))
            else:
                _log(f"Unknown key: <{key}>")
    return commands


async def runScriptLine(line):
    """Press all keys in a combo simultaneously, then release in reverse."""
    keys = convertLine(line)
    for k in keys:
        if k > 1000:
            consumerControl.press(int(k - 1000))
        else:
            kbd.press(k)
    for k in reversed(keys):
        if k > 1000:
            consumerControl.release()
        else:
            kbd.release(k)
    if _jitter_max_ms > 0:
        await asyncio.sleep(random.randint(_jitter_min_ms, _jitter_max_ms) / 1000.0)


async def sendString(line):
    """Inject a text string via HID keyboard."""
    if _jitter_max_ms > 0:
        for char in line:
            layout.write(char)
            await asyncio.sleep(random.randint(_jitter_min_ms, _jitter_max_ms) / 1000.0)
    else:
        layout.write(line, delay=0.002)


def replaceVariables(line):
    """Replace $VAR tokens with their current values (longest-first to avoid collisions)."""
    if '$' not in line:
        return line
    for var in sorted(variables.keys(), key=len, reverse=True):
        line = line.replace(var, str(variables[var]))
    for var in _INTERNAL_VAR_KEYS:
        line = line.replace(var, str(internalVariables[var]()))
    return line


def replaceDefines(line):
    """Replace DEFINE macros (longest-first to avoid collisions)."""
    if not defines:
        return line
    for key in sorted(defines.keys(), key=len, reverse=True):
        line = line.replace(key, defines[key])
    return line


def _safe_next(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None


# DuckyScript line parser
async def parseLine(line, script_lines):
    global defaultDelay, variables, functions, defines, _jitter_min_ms, _jitter_max_ms
    line = line.rstrip("\r\n").lstrip(" \t")
    if not line:
        return script_lines

    if "$_RANDOM_INT" in line:
        line = line.replace("$_RANDOM_INT", str(random.randint(
            int(variables.get("$_RANDOM_MIN", 0)),
            int(variables.get("$_RANDOM_MAX", 65535)))))
    line = replaceDefines(line)

    # INJECT_MOD strips prefix and executes remaining as key combo
    if line.startswith("INJECT_MOD"):
        await runScriptLine(line[11:])

    elif line.startswith("REM_BLOCK"):
        while True:
            line = _safe_next(script_lines)
            if line is None:
                _log("[WARN] REM_BLOCK missing END_REM.")
                break
            if line.strip().startswith("END_REM"):
                break

    elif line.startswith("REM"):
        pass

    elif line.startswith("JITTER"):
        args = line[7:].strip()
        if args.upper() == "OFF":
            _jitter_min_ms = 0
            _jitter_max_ms = 0
        else:
            parts = args.split()
            if len(parts) == 2:
                _jitter_min_ms = int(parts[0])
                _jitter_max_ms = int(parts[1])
            else:
                _log(f"[WARN] Invalid JITTER: {line}")

    elif line.startswith("HOLD"):
        kc = duckyKeys.get(line[5:].strip().upper())
        if kc:
            kbd.press(kc)
        else:
            _log(f"[WARN] Unknown HOLD key: {line}")

    elif line.startswith("RELEASE"):
        kc = duckyKeys.get(line[8:].strip().upper())
        if kc:
            kbd.release(kc)
        else:
            _log(f"[WARN] Unknown RELEASE key: {line}")

    elif line.startswith("DELAY"):
        line = replaceVariables(line)
        try:
            await asyncio.sleep(float(line[6:]) / 1000)
        except (ValueError, IndexError):
            _log(f"[WARN] Invalid DELAY: {line}")

    elif line.startswith("OVERCLOCK"):
        oc = line[10:].strip().upper()
        target = 125_000_000 if oc in ("DEFAULT", "125") else int(oc) * 1_000_000
        try:
            microcontroller.cpu.frequency = target
            _log(f"[OVERCLOCK] {target // 1_000_000}MHz")
        except Exception as e:
            _log(f"[OVERCLOCK ERROR] {e}")

    # STRINGLN multi-line block (exact match, no trailing content)
    elif line == "STRINGLN":
        line = _safe_next(script_lines)
        if line is None:
            _log("[WARN] STRINGLN block missing content.")
        else:
            line = line.rstrip("\r\n")
            while not line.lstrip(" \t").startswith("END_STRINGLN"):
                await sendString(replaceVariables(line))
                kbd.press(Keycode.ENTER)
                kbd.release(Keycode.ENTER)
                line = _safe_next(script_lines)
                if line is None:
                    _log("[WARN] STRINGLN block missing END_STRINGLN.")
                    break
                line = line.rstrip("\r\n")

    # STRINGLN single-line
    elif line.startswith("STRINGLN"):
        await sendString(replaceVariables(line[9:]))
        kbd.press(Keycode.ENTER)
        kbd.release(Keycode.ENTER)

    # STRING multi-line block (exact match, no trailing content)
    elif line == "STRING":
        line = _safe_next(script_lines)
        if line is None:
            _log("[WARN] STRING block missing content.")
        else:
            line = line.rstrip("\r\n")
            while not line.lstrip(" \t").startswith("END_STRING"):
                line = replaceVariables(line)
                line = replaceDefines(line)
                await sendString(line)
                line = _safe_next(script_lines)
                if line is None:
                    _log("[WARN] STRING block missing END_STRING.")
                    break
                line = line.rstrip("\r\n")

    # STRING single-line (note: 'STRING ' with space distinguishes from block)
    elif line.startswith("STRING "):
        await sendString(replaceVariables(line[7:]))

    elif line.startswith("ALTSTRING"):
        keys = replaceVariables(line[10:])
        for char in keys:
            if ('a' <= char <= 'z') or ('A' <= char <= 'Z') or ('0' <= char <= '9') or char == ' ':
                layout.write(char)
                await asyncio.sleep(0.005)
            else:
                kbd.press(Keycode.ALT)
                await asyncio.sleep(0.005)
                for digit in f"{ord(char):04d}":
                    kbd.press(_NUMPAD_MAP[digit])
                    await asyncio.sleep(0.005)
                    kbd.release(_NUMPAD_MAP[digit])
                    await asyncio.sleep(0.005)
                kbd.release(Keycode.ALT)
                await asyncio.sleep(0.005)

    elif line.startswith("PRINT"):
        _log("[SCRIPT] " + replaceVariables(line[6:]))

    elif line.startswith("IMPORT"):
        await runScript(line[7:])

    elif line.startswith("DEFAULT_DELAY"):
        defaultDelay = int(line[14:])
    elif line.startswith("DEFAULTDELAY"):
        defaultDelay = int(line[13:])

    elif line.startswith("LED"):
        if _led_ref is not None:
            if line.startswith("LED_OFF"):
                _led_ref.duty_cycle = 0
            elif line.startswith("LED_R") or line.startswith("LED_G"):
                _led_ref.duty_cycle = 65535
            else:
                _led_ref.duty_cycle = 0 if _led_ref.duty_cycle > 0 else 65535

    elif line.startswith("VAR"):
        match = _RE_VAR_DECL.match(line)
        if match:
            variables[f"${match.group(1)}"] = evaluateExpression(match.group(2))
        else:
            _log(f"[ERROR] Invalid VAR: {line}")

    elif line.startswith("$"):
        match = _RE_VAR_UPDATE.match(line)
        if match:
            variables[f"${match.group(1)}"] = evaluateExpression(match.group(2))
        else:
            _log(f"[ERROR] Invalid variable update: {line}")

    elif line.startswith("DEFINE"):
        parts = line.split(" ", 2)
        if len(parts) >= 3:
            defines[parts[1]] = parts[2]
        else:
            _log(f"[WARN] Invalid DEFINE: {line}")

    elif line.startswith("FUNCTION"):
        func_name = line.split()[1]
        functions[func_name] = []
        line = _safe_next(script_lines)
        while line is not None:
            cleaned = line.rstrip("\r\n").lstrip(" \t")
            if cleaned.strip() == "END_FUNCTION":
                break
            functions[func_name].append(cleaned)
            line = _safe_next(script_lines)
        else:
            _log(f"[WARN] FUNCTION '{func_name}' missing END_FUNCTION.")

    elif line.startswith("WHILE"):
        condition = line[5:].strip()
        loop_code = list(_getCodeBlock(script_lines))
        for _ in range(_WHILE_MAX_ITERATIONS):
            if not evaluateExpression(condition):
                break
            it = iter(loop_code)
            while True:
                ln = _safe_next(it)
                if ln is None:
                    break
                it = await parseLine(ln, it)
        else:
            _log(f"[WARN] WHILE exceeded {_WHILE_MAX_ITERATIONS} iterations.")

    elif line.upper().startswith("IF"):
        script_lines, _ = await IF(_getIfCondition(line), script_lines).runIf()

    elif line.upper().startswith("END_IF"):
        pass

    elif line == "RANDOM_LOWERCASE_LETTER":
        await sendString(random.choice(LETTERS))
    elif line == "RANDOM_UPPERCASE_LETTER":
        await sendString(random.choice(LETTERS_UPPER))
    elif line == "RANDOM_LETTER":
        await sendString(random.choice(LETTERS + LETTERS_UPPER))
    elif line == "RANDOM_NUMBER":
        await sendString(random.choice(NUMBERS))
    elif line == "RANDOM_SPECIAL":
        await sendString(random.choice(SPECIAL_CHARS))
    elif line == "RANDOM_CHAR":
        await sendString(random.choice(ALL_CHARS))
    elif line == "VID_RANDOM" or line == "PID_RANDOM":
        for _ in range(4):
            await sendString(random.choice(HEX_CHARS))
    elif line == "MAN_RANDOM" or line == "PROD_RANDOM":
        for _ in range(12):
            await sendString(random.choice(ALPHANUM_CHARS))
    elif line == "SERIAL_RANDOM":
        for _ in range(12):
            await sendString(random.choice(ALL_CHARS))

    elif line == "RESET":
        kbd.release_all()

    elif line == "SAVE_HOST_KEYBOARD_LOCK_STATE":
        _save_keyboard_led_state()
    elif line == "RESTORE_HOST_KEYBOARD_LOCK_STATE":
        _restore_keyboard_led_state()

    elif line == "WAIT_FOR_SCROLL_CHANGE":
        prev = _scrollOn()
        start = time.monotonic()
        while (time.monotonic() - start) < _SCROLL_WAIT_TIMEOUT_SEC:
            if _scrollOn() != prev:
                break
            await asyncio.sleep(0.01)
        else:
            _log(f"[WARN] WAIT_FOR_SCROLL_CHANGE timed out ({_SCROLL_WAIT_TIMEOUT_SEC}s).")

    elif line in functions:
        func_iter = iter(functions[line])
        safety = 0
        while True:
            func_line = _safe_next(func_iter)
            if func_line is None:
                break
            safety += 1
            if safety > _WHILE_MAX_ITERATIONS:
                _log(f"[WARN] Function '{line}' exceeded safety limit.")
                break
            func_iter = await parseLine(func_line, func_iter)

    elif line.startswith("CHAIN"):
        for chain_file in line[6:].strip().split():
            path = f"/sd/{chain_file}" if not chain_file.startswith("/") else chain_file
            if file_exists(path):
                _log(f"[CHAIN] {path}")
                await runScript(path)
            else:
                _log(f"[CHAIN ERROR] Not found: {path}")

    elif line.startswith("MOUSE_MOVE"):
        if mouse:
            parts = line[11:].strip().split()
            mouse.move(
                int(parts[0]) if parts else 0,
                int(parts[1]) if len(parts) > 1 else 0,
            )
        else:
            _log("[WARN] MOUSE_MOVE: Mouse HID not enabled.")
    elif line.startswith("MOUSE_CLICK"):
        if mouse:
            mouse.click(_MOUSE_BUTTONS.get(line[12:].strip().upper(), Mouse.LEFT_BUTTON))
        else:
            _log("[WARN] MOUSE_CLICK: Mouse HID not enabled.")
    elif line.startswith("MOUSE_HOLD"):
        if mouse:
            mouse.press(_MOUSE_BUTTONS.get(line[11:].strip().upper(), Mouse.LEFT_BUTTON))
        else:
            _log("[WARN] MOUSE_HOLD: Mouse HID not enabled.")
    elif line.startswith("MOUSE_RELEASE"):
        if mouse:
            name = line[14:].strip().upper()
            if name:
                mouse.release(_MOUSE_BUTTONS.get(name, Mouse.LEFT_BUTTON))
            else:
                mouse.release_all()
        else:
            _log("[WARN] MOUSE_RELEASE: Mouse HID not enabled.")
    elif line.startswith("MOUSE_SCROLL"):
        if mouse:
            mouse.move(0, 0, int(line[13:].strip()))
        else:
            _log("[WARN] MOUSE_SCROLL: Mouse HID not enabled.")

    else:
        await runScriptLine(line)

    return script_lines


# Hardware status
def getProgrammingStatus():
    """Returns True if the setup jumper/pin is active."""
    return not progStatusPin.value


# Script execution engine
async def runScript(file_path):
    global defaultDelay
    if not file_path:
        _log("[ERROR] No payload path.")
        return

    if not file_path.startswith("/sd/"):
        file_path = f"/sd/{file_path.lstrip('/')}"

    gc.collect()

    restart = True
    while restart:
        restart = False
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                prev_line = ""
                script_lines = f
                while True:
                    line = _safe_next(script_lines)
                    if line is None:
                        break
                    line_s = line.strip()
                    if not line_s:
                        continue

                    _log(f"[EXEC] {line_s}")

                    if line_s.startswith("REPEAT"):
                        try:
                            count = int(line_s[7:].strip())
                            for _ in range(count):
                                script_lines = await parseLine(prev_line, script_lines)
                                if defaultDelay > 0:
                                    await asyncio.sleep(defaultDelay / 1000.0)
                        except ValueError:
                            _log(f"[ERROR] Invalid REPEAT: {line_s}")

                    elif line_s.startswith("RESTART_PAYLOAD"):
                        kbd.release_all()
                        restart = True
                        break

                    elif line_s.startswith("STOP_PAYLOAD"):
                        break

                    else:
                        script_lines = await parseLine(line_s, script_lines)
                        prev_line = line_s

                    if defaultDelay > 0:
                        await asyncio.sleep(defaultDelay / 1000.0)

        except OSError as e:
            _log(f"[FATAL] {file_path}: {e}")
        finally:
            kbd.release_all()
            gc.collect()


# Filesystem utilities
def file_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def selectPayload():
    """Decode 4-bit DIP switch to resolve SD payload path (0-15)."""
    pins = (payload1Pin, payload2Pin, payload3Pin, payload4Pin)
    idx = 0
    try:
        for bit, pin in enumerate(pins):
            if not pin.value:
                idx |= (1 << bit)
    except Exception as e:
        _log(f"[WARN] DIP switch read error: {e}")
        idx = 0

    target = "/sd/payload.dd" if idx == 0 else f"/sd/payload{idx}.dd"
    if file_exists(target):
        return target

    default = "/sd/payload.dd"
    if target != default and file_exists(default):
        _log(f"[WARN] '{target}' not found, using default.")
        return default

    _log("[CRITICAL] Default payload missing. Scanning SD...")
    try:
        for f in os.listdir("/sd"):
            if f.endswith(".dd") and not f.startswith("._"):
                path = f"/sd/{f}"
                _log(f"[WARN] Emergency fallback: {path}")
                return path
    except Exception as e:
        _log(f"[CRITICAL] SD access failure: {e}")

    _log("[ERROR] No .dd payloads found.")
    return None


# Async background tasks
async def blink_pico_led(led):
    """Breathing LED effect. Injects LED reference for parseLine commands."""
    _set_led_ref(led)
    phase = False
    while True:
        if variables.get("$_EXFIL_LEDS_ENABLED"):
            led.duty_cycle = 65535
            await asyncio.sleep(0.1)
        else:
            seq = _LED_FADE_UP if phase else _LED_FADE_DOWN
            for dc in seq:
                led.duty_cycle = dc
                await asyncio.sleep(0.06)
            phase = not phase


async def monitor_led_changes():
    """Exfiltration: capture Num/Caps/Scroll Lock changes to /sd/loot.bin."""
    while True:
        if variables.get("$_EXFIL_MODE_ENABLED"):
            try:
                bits = []
                last_caps = _capsOn()
                last_num = _numOn()
                last_scroll = _scrollOn()
                start = time.monotonic()

                with open("/sd/loot.bin", "ab") as loot:
                    while variables.get("$_EXFIL_MODE_ENABLED"):
                        if (time.monotonic() - start) > _EXFIL_TIMEOUT_SEC:
                            _log(f"[WARN] Exfil timeout ({_EXFIL_TIMEOUT_SEC}s).")
                            variables["$_EXFIL_MODE_ENABLED"] = False
                            break

                        caps = _capsOn()
                        num = _numOn()
                        scroll = _scrollOn()

                        if caps != last_caps:
                            bits.append(0)
                            last_caps = caps
                        elif num != last_num:
                            bits.append(1)
                            last_num = num

                        if len(bits) == 8:
                            byte = 0
                            for b in bits:
                                byte = (byte << 1) | b
                            loot.write(bytes([byte]))
                            bits.clear()

                        if scroll != last_scroll:
                            variables["$_EXFIL_LEDS_ENABLED"] = False
                            break

                        await asyncio.sleep(0.01)
            except OSError as e:
                _log(f"[EXFIL ERROR] SD write: {e}")
            except Exception as e:
                _log(f"[EXFIL ERROR] {e}")

        await asyncio.sleep(0.1)