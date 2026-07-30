# License: GPLv2.0
# Copyright (c) 2026  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)
#
# Modified and adapted by:
# Copyright (c) 2026  Pedro Pacheco
# Copyright (c) 2026  Nahum Silvestre Martinez
# - RP2040 hardware adaptation and system modifications.
#
import gc
import os
import re
import time
import random
import board
import asyncio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from pins import (
    progStatusPin,
    payload1Pin,
    payload2Pin,
    payload3Pin,
    payload4Pin,
)

# comment out these lines for non_US keyboards
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout
from adafruit_hid.keycode import Keycode

# uncomment these lines for non_US keyboards
# replace LANG with appropriate language
#from keyboard_layout_win_LANG import KeyboardLayout as KeyboardLayout
#from keycode_win_LANG import Keycode

# ── Public API (controls `from duckyinpython import *`) ──────────────
__all__ = [
    "runScript",
    "selectPayload",
    "file_exists",
    "getProgrammingStatus",
    "blink_pico_led",
    "monitor_led_changes",
    "variables",
]

# ── HID Device Initialization ────────────────────────────────────────
kbd = Keyboard(usb_hid.devices)
consumerControl = ConsumerControl(usb_hid.devices)
layout = KeyboardLayout(kbd)

defaultDelay = 0

# ── LED State Helpers ────────────────────────────────────────────────

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

# ── Keycode Mapping Tables ───────────────────────────────────────────

duckyKeys = {
    'WINDOWS': Keycode.GUI, 'RWINDOWS': Keycode.RIGHT_GUI, 'GUI': Keycode.GUI, 'RGUI': Keycode.RIGHT_GUI, 'COMMAND': Keycode.GUI, 'RCOMMAND': Keycode.RIGHT_GUI,
    'APP': Keycode.APPLICATION, 'MENU': Keycode.APPLICATION, 'SHIFT': Keycode.SHIFT, 'RSHIFT': Keycode.RIGHT_SHIFT,
    'ALT': Keycode.ALT, 'RALT': Keycode.RIGHT_ALT, 'OPTION': Keycode.ALT, 'ROPTION': Keycode.RIGHT_ALT, 'CONTROL': Keycode.CONTROL, 'CTRL': Keycode.CONTROL, 'RCTRL': Keycode.RIGHT_CONTROL,
    'DOWNARROW': Keycode.DOWN_ARROW, 'DOWN': Keycode.DOWN_ARROW, 'LEFTARROW': Keycode.LEFT_ARROW,
    'LEFT': Keycode.LEFT_ARROW, 'RIGHTARROW': Keycode.RIGHT_ARROW, 'RIGHT': Keycode.RIGHT_ARROW,
    'UPARROW': Keycode.UP_ARROW, 'UP': Keycode.UP_ARROW, 'BREAK': Keycode.PAUSE,
    'PAUSE': Keycode.PAUSE, 'CAPSLOCK': Keycode.CAPS_LOCK, 'DELETE': Keycode.DELETE,
    'END': Keycode.END, 'ESC': Keycode.ESCAPE, 'ESCAPE': Keycode.ESCAPE, 'HOME': Keycode.HOME,
    'INSERT': Keycode.INSERT, 'NUMLOCK': Keycode.KEYPAD_NUMLOCK, 'PAGEUP': Keycode.PAGE_UP,
    'PAGEDOWN': Keycode.PAGE_DOWN, 'PRINTSCREEN': Keycode.PRINT_SCREEN, 'ENTER': Keycode.ENTER,
    'SCROLLLOCK': Keycode.SCROLL_LOCK, 'SPACE': Keycode.SPACE, 'TAB': Keycode.TAB,
    'BACKSPACE': Keycode.BACKSPACE,
    'A': Keycode.A, 'B': Keycode.B, 'C': Keycode.C, 'D': Keycode.D, 'E': Keycode.E,
    'F': Keycode.F, 'G': Keycode.G, 'H': Keycode.H, 'I': Keycode.I, 'J': Keycode.J,
    'K': Keycode.K, 'L': Keycode.L, 'M': Keycode.M, 'N': Keycode.N, 'O': Keycode.O,
    'P': Keycode.P, 'Q': Keycode.Q, 'R': Keycode.R, 'S': Keycode.S, 'T': Keycode.T,
    'U': Keycode.U, 'V': Keycode.V, 'W': Keycode.W, 'X': Keycode.X, 'Y': Keycode.Y,
    'Z': Keycode.Z, 'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3,
    'F4': Keycode.F4, 'F5': Keycode.F5, 'F6': Keycode.F6, 'F7': Keycode.F7,
    'F8': Keycode.F8, 'F9': Keycode.F9, 'F10': Keycode.F10, 'F11': Keycode.F11,
    'F12': Keycode.F12, 'F13': Keycode.F13, 'F14': Keycode.F14, 'F15': Keycode.F15,
    'F16': Keycode.F16, 'F17': Keycode.F17, 'F18': Keycode.F18, 'F19': Keycode.F19,
    'F20': Keycode.F20, 'F21': Keycode.F21, 'F22': Keycode.F22, 'F23': Keycode.F23,
    'F24': Keycode.F24
}
duckyConsumerKeys = {
    'MK_VOLUP': ConsumerControlCode.VOLUME_INCREMENT, 'MK_VOLDOWN': ConsumerControlCode.VOLUME_DECREMENT, 'MK_MUTE': ConsumerControlCode.MUTE,
    'MK_NEXT': ConsumerControlCode.SCAN_NEXT_TRACK, 'MK_PREV': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
    'MK_PP': ConsumerControlCode.PLAY_PAUSE, 'MK_STOP': ConsumerControlCode.STOP
}

# ── Runtime State ────────────────────────────────────────────────────

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
defines = {}
functions = {}

# ── Character Sets (pre-allocated, immutable) ────────────────────────

LETTERS = "abcdefghijklmnopqrstuvwxyz"
LETTERS_UPPER = LETTERS.upper()
NUMBERS = "0123456789"
SPECIAL_CHARS = "!@#$%^&*()"
ALL_CHARS = LETTERS + LETTERS_UPPER + NUMBERS + SPECIAL_CHARS
HEX_CHARS = NUMBERS + "ABCDEF"
ALPHANUM_CHARS = LETTERS + LETTERS_UPPER + NUMBERS

# ── Pre-compiled Regex (avoid re-compilation per line) ───────────────

_RE_VAR_DECL = re.compile(r"VAR\s+\$(\w+)\s*=\s*(.+)")
_RE_VAR_UPDATE = re.compile(r"\$(\w+)\s*=\s*(.+)")
_RE_TRUE = re.compile(r'[Tt][Rr][Uu][Ee]')
_RE_FALSE = re.compile(r'[Ff][Aa][Ll][Ss][Ee]')

# ── Safety Limits ────────────────────────────────────────────────────

_WHILE_MAX_ITERATIONS = 100_000
_SCROLL_WAIT_TIMEOUT_SEC = 120
_EXFIL_TIMEOUT_SEC = 3600  # 1 hour max exfiltration session

# ── Pre-computed Numpad Keycode Map ──────────────────────────────────

NUMPAD_MAP = {
    '0': Keycode.KEYPAD_ZERO, '1': Keycode.KEYPAD_ONE,
    '2': Keycode.KEYPAD_TWO, '3': Keycode.KEYPAD_THREE,
    '4': Keycode.KEYPAD_FOUR, '5': Keycode.KEYPAD_FIVE,
    '6': Keycode.KEYPAD_SIX, '7': Keycode.KEYPAD_SEVEN,
    '8': Keycode.KEYPAD_EIGHT, '9': Keycode.KEYPAD_NINE
}

# ── LED reference (injected by code.py via blink_pico_led parameter) ─
# This module does NOT create the PWMOut; code.py owns it.
# For parseLine LED commands, we use a module-level reference.
_led_ref = None


def _set_led_ref(led_obj):
    """Called by code.py to inject the PWMOut LED reference."""
    global _led_ref
    _led_ref = led_obj


# ── IF/ELSE/END_IF Block Handler ─────────────────────────────────────

class IF:
    def __init__(self, condition, code_lines):
        self.condition = condition
        self.code_lines = list(code_lines)
        self._idx = 0
        self.lastIfResult = None

    def _pop_line(self):
        """O(1) line retrieval using index instead of list.pop(0)."""
        if self._idx >= len(self.code_lines):
            return None
        line = self.code_lines[self._idx]
        self._idx += 1
        return line

    def _remaining_lines(self):
        """Return remaining unprocessed lines as a new list."""
        return self.code_lines[self._idx:]

    def _exitIf(self):
        _depth = 0
        while self._idx < len(self.code_lines):
            line = self._pop_line().strip()
            if line.upper().startswith("END_IF"):
                _depth -= 1
            elif line.upper().startswith("IF"):
                _depth += 1
            if _depth < 0:
                break
        return self._remaining_lines()

    async def runIf(self):
        if isinstance(self.condition, str):
            self.lastIfResult = evaluateExpression(self.condition)
        elif isinstance(self.condition, bool):
            self.lastIfResult = self.condition
        else:
            raise ValueError("Invalid condition type")

        depth = 0
        while self._idx < len(self.code_lines):
            line = self._pop_line().strip()
            if not line:
                continue

            if line.startswith("IF"):
                depth += 1
            elif line.startswith("END_IF"):
                if depth == 0:
                    return (self._remaining_lines(), -1)
                depth -= 1

            elif line.startswith("ELSE") and depth == 0:
                if self.lastIfResult is False:
                    line = line[4:].strip()
                    if line.startswith("IF"):
                        nestedCondition = _getIfCondition(line)
                        remaining = self._remaining_lines()
                        remaining, self.lastIfResult = await IF(nestedCondition, remaining).runIf()
                        if self.lastIfResult == -1 or self.lastIfResult is True:
                            return (remaining, True)
                    else:
                        remaining = self._remaining_lines()
                        return await IF(True, remaining).runIf()
                else:
                    self.code_lines = self._remaining_lines()
                    self._idx = 0
                    self._exitIf()
                    break

            # Process regular lines
            elif self.lastIfResult:
                remaining = self._remaining_lines()
                remaining = list(await parseLine(line, iter(remaining)))
                self.code_lines = remaining
                self._idx = 0
        return (self._remaining_lines(), self.lastIfResult)


def _getIfCondition(line):
    return str(line)[2:-4].strip()


def _isCodeBlock(line):
    upper = line.upper().strip()
    return upper.startswith("IF") or upper.startswith("WHILE")


def _getCodeBlock(linesIter):
    """Returns the code block starting at the given line."""
    code = []
    depth = 1
    for line in linesIter:
        line = line.strip()
        if line.upper().startswith("END_"):
            depth -= 1
        elif _isCodeBlock(line):
            depth += 1
        if depth <= 0:
            break
        code.append(line)
    return code


# ── Expression Evaluator (Recursive Descent Parser) ──────────────────

def evaluateExpression(expression):
    """Safely evaluate a DuckyScript expression using recursive descent parser."""
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
        if _peek() == 'not' or _peek() == '!':
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
        if _peek() == '**' or _peek() == '^':
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
    """Tokenize an expression string into operator and operand tokens."""
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


# ── Keycode Conversion & String Injection ────────────────────────────

def convertLine(line):
    commands = []
    # loop on each key - the filter removes empty values
    for key in filter(None, line.split(" ")):
        key = key.upper()
        # find the keycode for the command in the list
        command_keycode = duckyKeys.get(key, None)
        command_consumer_keycode = duckyConsumerKeys.get(key, None)
        if command_keycode is not None:
            commands.append(command_keycode)
        elif command_consumer_keycode is not None:
            commands.append(1000 + command_consumer_keycode)
        elif hasattr(Keycode, key):
            commands.append(getattr(Keycode, key))
        else:
            print(f"Unknown key: <{key}>")

    return commands


def runScriptLine(line):
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


def sendString(line):
    layout.write(line)


def replaceVariables(line):
    # Fast-path: skip iteration if no variable markers present
    if '$' not in line:
        return line
    for var in variables:
        line = line.replace(var, str(variables[var]))
    for var in internalVariables:
        line = line.replace(var, str(internalVariables[var]()))
    return line


def replaceDefines(line):
    if not defines:
        return line
    for define, value in defines.items():
        line = line.replace(define, value)
    return line


def _safe_next(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None


# ── DuckyScript Line Parser ──────────────────────────────────────────

async def parseLine(line, script_lines):
    global defaultDelay, variables, functions, defines
    line = line.strip()
    line = line.replace("$_RANDOM_INT", str(random.randint(int(variables.get("$_RANDOM_MIN", 0)), int(variables.get("$_RANDOM_MAX", 65535)))))
    line = replaceDefines(line)
    if line.startswith("INJECT_MOD"):
        line = line[11:]
    elif line.startswith("REM_BLOCK"):
        while not line.startswith("END_REM"):
            line = _safe_next(script_lines)
            if line is None:
                print("[WARN] REM_BLOCK missing END_REM, reached end of script.")
                break
            line = line.strip()
    elif line.startswith("REM"):
        pass
    elif line.startswith("HOLD"):
        # HOLD command to press and hold a key
        key = line[5:].strip().upper()
        commandKeycode = duckyKeys.get(key, None)
        if commandKeycode:
            kbd.press(commandKeycode)
        else:
            print(f"Unknown key to HOLD: <{key}>")
    elif line.startswith("RELEASE"):
        # RELEASE command to release a held key
        key = line[8:].strip().upper()
        commandKeycode = duckyKeys.get(key, None)
        if commandKeycode:
            kbd.release(commandKeycode)
        else:
            print(f"Unknown key to RELEASE: <{key}>")
    elif line.startswith("DELAY"):
        line = replaceVariables(line)
        await asyncio.sleep(float(line[6:]) / 1000)
    elif line == "STRINGLN":               #< stringLN block
        line = _safe_next(script_lines)
        if line is None:
            print("[WARN] STRINGLN block missing content.")
        else:
            line = line.strip()
            # Check END marker BEFORE variable/define replacement
            while not line.startswith("END_STRINGLN"):
                line = replaceVariables(line)
                sendString(line)
                kbd.press(Keycode.ENTER)
                kbd.release(Keycode.ENTER)
                line = _safe_next(script_lines)
                if line is None:
                    print("[WARN] STRINGLN block missing END_STRINGLN.")
                    break
                line = line.strip()
    elif line.startswith("STRINGLN"):
        sendString(replaceVariables(line[9:]))
        kbd.press(Keycode.ENTER)
        kbd.release(Keycode.ENTER)
    elif line == "STRING":                 #< string block
        line = _safe_next(script_lines)
        if line is None:
            print("[WARN] STRING block missing content.")
        else:
            line = line.strip()
            # Check END marker BEFORE variable/define replacement
            while not line.startswith("END_STRING"):
                line = replaceVariables(line)
                line = replaceDefines(line)
                sendString(line)
                line = _safe_next(script_lines)
                if line is None:
                    print("[WARN] STRING block missing END_STRING.")
                    break
                line = line.strip()
    elif line.startswith("STRING"):
        sendString(replaceVariables(line[7:]))
    elif line.startswith("ALTSTRING"):
        keys = replaceVariables(line[10:])

        for char in keys:
            # Fast path: Inject alphanumeric characters and spaces directly
            if (char >= 'a' and char <= 'z') or (char >= 'A' and char <= 'Z') or (char >= '0' and char <= '9') or char == ' ':
                layout.write(char)
                await asyncio.sleep(0.005)

            # Slow path: Inject symbols via Numpad ALT codes for layout evasion
            else:
                kbd.press(Keycode.ALT)
                await asyncio.sleep(0.005)

                for digit in f"{ord(char):04d}":
                    kbd.press(NUMPAD_MAP[digit])
                    await asyncio.sleep(0.005)
                    kbd.release(NUMPAD_MAP[digit])
                    await asyncio.sleep(0.005)

                kbd.release(Keycode.ALT)
                await asyncio.sleep(0.005)
    elif line.startswith("PRINT"):
        line = replaceVariables(line[6:])
        print("[SCRIPT]: " + line)
    elif line.startswith("IMPORT"):
        await runScript(line[7:])
    elif line.startswith("DEFAULT_DELAY"):
        defaultDelay = int(line[14:])
    elif line.startswith("DEFAULTDELAY"):
        defaultDelay = int(line[13:])
    elif line.startswith("LED_OFF"):
        if _led_ref is not None:
            _led_ref.duty_cycle = 0
    elif line.startswith("LED_R"):
        if _led_ref is not None:
            _led_ref.duty_cycle = 65535
    elif line.startswith("LED_G"):
        if _led_ref is not None:
            _led_ref.duty_cycle = 65535
    elif line.startswith("LED"):
        if _led_ref is not None:
            _led_ref.duty_cycle = 0 if _led_ref.duty_cycle > 0 else 65535

    elif line.startswith("VAR"):
        match = _RE_VAR_DECL.match(line)
        if match:
            varName = f"${match.group(1)}"
            value = evaluateExpression(match.group(2))
            variables[varName] = value
        else:
            raise SyntaxError(f"Invalid variable declaration: {line}")
    elif line.startswith("$"):
        match = _RE_VAR_UPDATE.match(line)
        if match:
            varName = f"${match.group(1)}"
            value = evaluateExpression(match.group(2))
            variables[varName] = value
        else:
            raise SyntaxError(f"Invalid variable update, declare variable first: {line}")
    elif line.startswith("DEFINE"):
        defineLocation = line.find(" ")
        valueLocation = line.find(" ", defineLocation + 1)
        defineName = line[defineLocation+1:valueLocation]
        defineValue = line[valueLocation+1:]
        defines[defineName] = defineValue
    elif line.startswith("FUNCTION"):
        func_name = line.split()[1]
        functions[func_name] = []
        line = _safe_next(script_lines)
        while line is not None and line.strip() != "END_FUNCTION":
            functions[func_name].append(line.strip())
            line = _safe_next(script_lines)
        if line is None:
            print(f"[WARN] FUNCTION '{func_name}' missing END_FUNCTION.")
    elif line.startswith("WHILE"):
        condition = line[5:].strip()
        loopCode = list(_getCodeBlock(script_lines))
        for _iter_count in range(_WHILE_MAX_ITERATIONS):
            if not evaluateExpression(condition):
                break
            # Iterate over loopCode by index — no copy per iteration
            idx = 0
            while idx < len(loopCode):
                remaining = iter(loopCode[idx + 1:])
                remaining = await parseLine(loopCode[idx], remaining)
                idx += 1
        else:
            print(f"[WARN] WHILE loop exceeded {_WHILE_MAX_ITERATIONS} iterations. Breaking.")

    elif line.upper().startswith("IF"):
        script_lines, ret = await IF(_getIfCondition(line), script_lines).runIf()
    elif line.upper().startswith("END_IF"):
        pass
    elif line == "RANDOM_LOWERCASE_LETTER":
        sendString(random.choice(LETTERS))
    elif line == "RANDOM_UPPERCASE_LETTER":
        sendString(random.choice(LETTERS_UPPER))
    elif line == "RANDOM_LETTER":
        sendString(random.choice(LETTERS + LETTERS_UPPER))
    elif line == "RANDOM_NUMBER":
        sendString(random.choice(NUMBERS))
    elif line == "RANDOM_SPECIAL":
        sendString(random.choice(SPECIAL_CHARS))
    elif line == "RANDOM_CHAR":
        sendString(random.choice(ALL_CHARS))
    elif line == "VID_RANDOM" or line == "PID_RANDOM":
        for _ in range(4):
            sendString(random.choice(HEX_CHARS))
    elif line == "MAN_RANDOM" or line == "PROD_RANDOM":
        for _ in range(12):
            sendString(random.choice(ALPHANUM_CHARS))
    elif line == "SERIAL_RANDOM":
        for _ in range(12):
            sendString(random.choice(ALL_CHARS))
    elif line == "RESET":
        kbd.release_all()
    elif line == "SAVE_HOST_KEYBOARD_LOCK_STATE":
        _save_keyboard_led_state()
    elif line == "RESTORE_HOST_KEYBOARD_LOCK_STATE":
        _restore_keyboard_led_state()
    elif line == "WAIT_FOR_SCROLL_CHANGE":
        last_scroll_state = _scrollOn()
        _wait_start = time.monotonic()
        while (time.monotonic() - _wait_start) < _SCROLL_WAIT_TIMEOUT_SEC:
            current_scroll_state = _scrollOn()
            if current_scroll_state != last_scroll_state:
                break
            await asyncio.sleep(0.01)
        else:
            print(f"[WARN] WAIT_FOR_SCROLL_CHANGE timed out after {_SCROLL_WAIT_TIMEOUT_SEC}s.")
    elif line in functions:
        updated_lines = []
        inside_while_block = False
        for func_line in functions[line]:
            if func_line.startswith("WHILE"):
                inside_while_block = True
                updated_lines.append(func_line)
            elif func_line.startswith("END_WHILE"):
                inside_while_block = False
                updated_lines.append(func_line)
                await parseLine(updated_lines[0], iter(updated_lines))
                updated_lines = []
            elif inside_while_block:
                updated_lines.append(func_line)
            elif not (func_line.startswith("END_WHILE") or func_line.startswith("WHILE")):
                await parseLine(func_line, iter(functions[line]))
    else:
        runScriptLine(line)

    return iter(script_lines)


# ── Hardware Status ──────────────────────────────────────────────────

def getProgrammingStatus():
    """Returns True if the setup jumper/pin is active."""
    return not progStatusPin.value


# ── Script Execution Engine ──────────────────────────────────────────

async def runScript(file_path):
    global defaultDelay

    if not file_path:
        print("[ERROR] Execution aborted: Payload path is empty.")
        return

    # Force execution ONLY from SD Card as requested
    if not file_path.startswith("/sd/"):
        file_path = f"/sd/{file_path.lstrip('/')}"

    gc.collect()  # Pre-execution memory cleanup

    restart = True
    while restart:
        restart = False
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                # Lazy line-by-line reading: file object is its own iterator
                # This avoids loading the entire script into RAM at once
                previous_line = ""
                lines_buffer = []

                for raw_line in f:
                    lines_buffer.append(raw_line)

                script_lines = iter(lines_buffer)
                while True:
                    line = _safe_next(script_lines)
                    if line is None:
                        break

                    line_stripped = line.strip()
                    if not line_stripped:
                        continue

                    print(f"[EXEC] {line_stripped}")

                    if line_stripped.startswith("REPEAT"):
                        try:
                            repeats = int(line_stripped[7:].strip())
                            for _ in range(repeats):
                                script_lines = await parseLine(previous_line, script_lines)
                                await asyncio.sleep(defaultDelay / 1000.0)
                        except ValueError:
                            print(f"[ERROR] Invalid REPEAT syntax: {line_stripped}")

                    elif line_stripped.startswith("RESTART_PAYLOAD"):
                        kbd.release_all()
                        restart = True
                        break

                    elif line_stripped.startswith("STOP_PAYLOAD"):
                        restart = False
                        break

                    else:
                        script_lines = await parseLine(line_stripped, script_lines)
                        previous_line = line_stripped

                    await asyncio.sleep(defaultDelay / 1000.0)

        except OSError as e:
            print(f"[FATAL ERROR] Failed to execute {file_path} from SD Card. Details: {e}")
        finally:
            kbd.release_all()
            gc.collect()  # Post-execution memory cleanup


# ── Filesystem Utilities ─────────────────────────────────────────────

def file_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def selectPayload():
    """
    Decodes a 4-bit binary DIP switch to resolve the target SD payload path (0-15).
    Implements a 3-tier filesystem fallback strategy to prevent runtime faults.
    """
    # LSB to MSB mapping (Bit 0 to Bit 3)
    pins = (payload1Pin, payload2Pin, payload3Pin, payload4Pin)
    payload_index = 0

    try:
        for bit_position, pin in enumerate(pins):
            if not pin.value:
                payload_index |= (1 << bit_position)
    except Exception as e:
        print(f"[WARN] GPIO read exception on DIP switch: {e}. Defaulting to index 0.")
        payload_index = 0

    target_path = "/sd/payload.dd" if payload_index == 0 else f"/sd/payload{payload_index}.dd"

    # Tier 1: Exact target payload verification
    if file_exists(target_path):
        return target_path

    print(f"[WARN] Target '{target_path}' not found. Attempting Tier 2 fallback.")

    # Tier 2: Standard default payload fallback
    default_path = "/sd/payload.dd"
    if target_path != default_path and file_exists(default_path):
        return default_path

    # Tier 3: Emergency filesystem scan for any available .dd payload
    print("[CRITICAL] Default 'payload.dd' missing. Initiating emergency SD scan.")
    try:
        for file in os.listdir("/sd"):
            if file.endswith(".dd") and not file.startswith("._"):
                emergency_path = f"/sd/{file}"
                print(f"[WARN] Executing emergency fallback payload: {emergency_path}")
                return emergency_path
    except Exception as e:
        print(f"[CRITICAL] SD card filesystem access failure: {e}")

    print("[ERROR] No valid '.dd' payloads found on filesystem. Aborting execution.")
    return None


# ── Async Background Tasks ───────────────────────────────────────────

async def blink_pico_led(led):
    """Breathing LED effect. Also injects LED reference for parseLine commands."""
    _set_led_ref(led)
    led_state = False
    while True:
        if variables.get("$_EXFIL_LEDS_ENABLED"):
            led.duty_cycle = 65535
            await asyncio.sleep(0.1)
        else:
            # Reduced from 20 steps to 8 for fewer context switches
            if led_state:
                for i in (0, 14, 28, 42, 57, 71, 85, 100):
                    led.duty_cycle = int(i * 65535 / 100)  # Fade Up
                    await asyncio.sleep(0.06)
                led_state = False
            else:
                for i in (100, 85, 71, 57, 42, 28, 14, 0):
                    led.duty_cycle = int(i * 65535 / 100)  # Fade Down
                    await asyncio.sleep(0.06)
                led_state = True


async def monitor_led_changes():
    """
    Exfiltration mode: Reads Num/Caps/Scroll Lock state changes and
    saves the binary data strictly to /sd/loot.bin
    """
    while True:
        if variables.get("$_EXFIL_MODE_ENABLED"):
            try:
                bit_list = []
                last_caps_state = _capsOn()
                last_num_state = _numOn()
                last_scroll_state = _scrollOn()

                # Strict SD routing for loot
                loot_path = "/sd/loot.bin"
                _exfil_start = time.monotonic()

                with open(loot_path, "ab") as file:
                    while variables.get("$_EXFIL_MODE_ENABLED"):
                        # Safety timeout to prevent infinite exfiltration
                        if (time.monotonic() - _exfil_start) > _EXFIL_TIMEOUT_SEC:
                            print(f"[WARN] Exfiltration timeout after {_EXFIL_TIMEOUT_SEC}s.")
                            variables["$_EXFIL_MODE_ENABLED"] = False
                            break

                        caps_state = _capsOn()
                        num_state = _numOn()
                        scroll_state = _scrollOn()

                        if caps_state != last_caps_state:
                            bit_list.append(0)
                            last_caps_state = caps_state

                        elif num_state != last_num_state:
                            bit_list.append(1)
                            last_num_state = num_state

                        # Flush 1 byte to the SD card
                        if len(bit_list) == 8:
                            byte = 0
                            for b in bit_list:
                                byte = (byte << 1) | b
                            file.write(bytes([byte]))
                            bit_list.clear()

                        if scroll_state != last_scroll_state:
                            variables["$_EXFIL_LEDS_ENABLED"] = False
                            break

                        await asyncio.sleep(0.01)
            except OSError as e:
                print(f"[FATAL EXFIL ERROR] Could not write to SD Card: {e}")
            except Exception as e:
                print(f"[FATAL EXFIL ERROR] Core loop failed: {e}")

        await asyncio.sleep(0.1)