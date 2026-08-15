# -*- coding: utf-8 -*-

import sys
import os
import re
import time
import random
import shutil
import platform
import subprocess
from io import BytesIO
from urllib.request import urlopen, Request

from PIL import Image, ImageEnhance


# ============================================================
# CONFIG
# ============================================================

DEFAULT_IMAGE_URL = (
    "https://raw.githubusercontent.com/Ghosthszz/cmd/"
    "c8ee1a2fd69d37daeaa25144ad053431575da4fb/logo.jpg"
)

DEFAULT_WIDTH = 100

TYPE_SPEED = 0.006
MIN_WIDTH = 36
MAX_WIDTH = 160


# ============================================================
# TERMINAL DETECTION
# ============================================================

SYSTEM = platform.system().lower()

IS_WINDOWS = SYSTEM == "windows"
IS_MAC = SYSTEM == "darwin"
IS_LINUX = SYSTEM == "linux"

IS_TERMUX = (
    "com.termux" in os.environ.get("PREFIX", "").lower()
    or "termux" in os.environ.get("TERMUX_VERSION", "").lower()
)

TERM = os.environ.get("TERM", "").lower()
COLORTERM = os.environ.get("COLORTERM", "").lower()

IS_TTY = sys.stdout.isatty()

UTF8_OK = (
    (sys.stdout.encoding or "").lower().replace("-", "") in
    ("utf8", "utf_8", "cp65001")
)


def enable_windows_ansi():
    """
    Tenta habilitar ANSI no CMD/PowerShell moderno.
    Windows Terminal normalmente já suporta.
    """
    if not IS_WINDOWS:
        return True

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32

        handle = kernel32.GetStdHandle(-11)

        mode = ctypes.c_uint32()

        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

            if kernel32.SetConsoleMode(
                handle,
                mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            ):
                return True

    except Exception:
        pass

    return False


WINDOWS_ANSI = enable_windows_ansi()

ANSI_SUPPORTED = (
    IS_TTY
    and (
        not IS_WINDOWS
        or WINDOWS_ANSI
        or "ansicon" in os.environ
        or "wt_session" in {
            key.lower(): value
            for key, value in os.environ.items()
        }
    )
)

TRUECOLOR_SUPPORTED = (
    ANSI_SUPPORTED
    and (
        "truecolor" in COLORTERM
        or "24bit" in COLORTERM
        or IS_TERMUX
        or IS_MAC
        or "xterm" in TERM
        or "screen" in TERM
        or "tmux" in TERM
        or IS_WINDOWS
    )
)


# ============================================================
# SYMBOLS
# ============================================================

if UTF8_OK:
    CHAR_FULL = "━"
    CHAR_EMPTY = "─"
    CHAR_SIDE_L = "╺"
    CHAR_SIDE_R = "╸"
    CHAR_IMAGE = "▀"

    GLITCH_CHARS = "█▓▒░╱╲│─╳"
    SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

else:
    CHAR_FULL = "="
    CHAR_EMPTY = "-"
    CHAR_SIDE_L = "["
    CHAR_SIDE_R = "]"
    CHAR_IMAGE = "#"

    GLITCH_CHARS = "#%*@/\\|-X"
    SPINNER = ["|", "/", "-", "\\"]


# ============================================================
# ANSI
# ============================================================

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def ansi(code):
    if ANSI_SUPPORTED:
        return f"\033[{code}m"

    return ""


RESET = ansi("0")
BOLD = ansi("1")
DIM = ansi("2")

GREEN = ansi("38;2;0;255;120")
GREEN2 = ansi("38;2;0;210;90")
GREEN3 = ansi("38;2;120;255;170")

DARK_GREEN = ansi("38;2;0;105;50")
GRAY_GREEN = ansi("38;2;90;145;110")

WHITE = ansi("38;2;220;255;230")
RED = ansi("38;2;255;75;75")

BLACK_BG = ansi("40")

HIDE_CURSOR = "\033[?25l" if ANSI_SUPPORTED else ""
SHOW_CURSOR = "\033[?25h" if ANSI_SUPPORTED else ""


def fg(r, g, b):
    if not TRUECOLOR_SUPPORTED:
        return GREEN

    return f"\033[38;2;{r};{g};{b}m"


def bg(r, g, b):
    if not TRUECOLOR_SUPPORTED:
        return ""

    return f"\033[48;2;{r};{g};{b}m"


# ============================================================
# TERMINAL HELPERS
# ============================================================

def get_terminal_size():
    size = shutil.get_terminal_size(
        fallback=(100, 36)
    )

    return size.columns, size.lines


def cls():
    if ANSI_SUPPORTED:
        print("\033[2J\033[H", end="")
    else:
        os.system(
            "cls"
            if IS_WINDOWS
            else "clear"
        )


def visible_len(text):
    return len(
        ANSI_RE.sub("", text)
    )


def center(text, width):
    length = visible_len(text)

    if length >= width:
        return text

    padding = max(
        0,
        (width - length) // 2
    )

    return (" " * padding) + text


def get_safe_width(preferred=DEFAULT_WIDTH):
    terminal_width, _ = get_terminal_size()

    available = max(
        MIN_WIDTH,
        terminal_width - 2
    )

    preferred = max(
        MIN_WIDTH,
        min(preferred, MAX_WIDTH)
    )

    return min(
        preferred,
        available
    )


def get_render_height():
    _, terminal_height = get_terminal_size()

    reserved = 10

    return max(
        6,
        terminal_height - reserved
    )


def responsive_bar_size(width):
    return max(
        12,
        min(
            40,
            width - 20
        )
    )


# ============================================================
# TEXT EFFECTS
# ============================================================

def glitch(text, probability=0.025):
    pool = "/\\_|:.`~-=+*#"

    return "".join(
        random.choice(pool)
        if char != " " and random.random() < probability
        else char
        for char in text
    )


def type_line(text, color, width):
    padding = max(
        0,
        (width - visible_len(text)) // 2
    )

    prefix = " " * padding

    current = ""

    for char in text:
        current += char

        print(
            "\r"
            + prefix
            + color
            + current
            + RESET,
            end="",
            flush=True
        )

        time.sleep(TYPE_SPEED)

    print()


# ============================================================
# VISUAL COMPONENTS
# ============================================================

def horizontal_line(width):
    line_width = max(
        10,
        min(width, 76)
    )

    print(
        center(
            DARK_GREEN
            + CHAR_EMPTY * line_width
            + RESET,
            width
        )
    )


def header(width):
    print()

    print(
        center(
            BOLD
            + GREEN
            + "G H O S T   P R O T O C O L"
            + RESET,
            width
        )
    )

    print(
        center(
            DIM
            + GRAY_GREEN
            + "adaptive terminal rendering environment"
            + RESET,
            width
        )
    )

    print()

    horizontal_line(width)


def progress_bar(label, width, duration=0.9, color=GREEN):
    bar_size = responsive_bar_size(width)

    print()

    print(
        center(
            DIM
            + GRAY_GREEN
            + label
            + RESET,
            width
        )
    )

    for i in range(bar_size + 1):
        pct = int(
            i / bar_size * 100
        )

        filled = CHAR_FULL * i
        empty = CHAR_EMPTY * (bar_size - i)

        bar = (
            CHAR_SIDE_L
            + color
            + filled
            + RESET
            + DARK_GREEN
            + empty
            + RESET
            + CHAR_SIDE_R
        )

        content = (
            f"{bar} "
            f"{GREEN3}{pct:3d}%{RESET}"
        )

        print(
            "\r"
            + center(content, width),
            end="",
            flush=True
        )

        time.sleep(
            duration / bar_size
        )

    print()


def stuck_bar(label, width):
    bar_size = responsive_bar_size(width)

    print()

    print(
        center(
            DIM
            + GRAY_GREEN
            + label
            + RESET,
            width
        )
    )

    stop_at = max(
        1,
        bar_size - 1
    )

    for i in range(stop_at):
        pct = int(
            i / bar_size * 100
        )

        bar = (
            CHAR_SIDE_L
            + GREEN2
            + CHAR_FULL * i
            + RESET
            + DARK_GREEN
            + CHAR_EMPTY * (bar_size - i)
            + RESET
            + CHAR_SIDE_R
        )

        print(
            "\r"
            + center(
                f"{bar} {pct:3d}%",
                width
            ),
            end="",
            flush=True
        )

        time.sleep(0.025)

    for _ in range(4):
        pct = random.choice(
            [96, 97, 98, 99]
        )

        bar = (
            CHAR_SIDE_L
            + RED
            + CHAR_FULL * stop_at
            + RESET
            + CHAR_EMPTY
            + CHAR_SIDE_R
        )

        print(
            "\r"
            + center(
                f"{bar} {pct:3d}%",
                width
            ),
            end="",
            flush=True
        )

        time.sleep(0.28)

    final_bar = (
        CHAR_SIDE_L
        + GREEN3
        + CHAR_FULL * bar_size
        + RESET
        + CHAR_SIDE_R
    )

    print(
        "\r"
        + center(
            f"{final_bar} 100%",
            width
        )
    )


# ============================================================
# INTRO
# ============================================================

def intro(width):
    cls()

    print(
        BLACK_BG + HIDE_CURSOR,
        end=""
    )

    header(width)

    messages = [
        "[ INIT ] starting encrypted session",
        "[  OK  ] framebuffer initialized",
        "[  OK  ] terminal profile detected",
        "[ SCAN ] searching local trace",
        "[ MASK ] identity layer prepared",
    ]

    print()

    for message in messages:
        type_line(
            glitch(message, 0.01),
            GREEN,
            width
        )

        time.sleep(0.10)

    progress_bar(
        "injecting payload",
        width,
        0.8,
        GREEN
    )

    progress_bar(
        "decrypting sectors",
        width,
        0.9,
        GREEN2
    )

    stuck_bar(
        "forging identity mask",
        width
    )


# ============================================================
# SUSPENSE
# ============================================================

def suspense(width):
    messages = [
        "binding glyph layers",
        "injecting noise pattern",
        "stabilizing framebuffer",
        "forging image edges",
        "loading shadow matrix",
        "mapping luminance",
        "reconstructing source",
    ]

    print()

    for i in range(18):
        message = random.choice(
            messages
        )

        spinner = SPINNER[
            i % len(SPINNER)
        ]

        text = (
            DARK_GREEN
            + spinner
            + RESET
            + " "
            + DIM
            + GRAY_GREEN
            + message
            + RESET
        )

        print(
            "\r"
            + center(text, width),
            end="",
            flush=True
        )

        time.sleep(0.09)

    print(
        "\r"
        + center(
            GREEN3
            + "[ render matrix ready ]"
            + RESET,
            width
        )
    )

    time.sleep(0.35)


# ============================================================
# AUDIO
# ============================================================

def play_audio(path):
    if not path:
        return

    if IS_TERMUX and shutil.which(
        "termux-media-player"
    ):
        try:
            subprocess.Popen(
                [
                    "termux-media-player",
                    "play",
                    path
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


def stop_audio():
    if IS_TERMUX and shutil.which(
        "termux-media-player"
    ):
        try:
            subprocess.run(
                [
                    "termux-media-player",
                    "stop"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


# ============================================================
# IMAGE
# ============================================================

def fetch_online_image(url):
    req = Request(
        url,
        headers={
            "User-Agent":
                "Mozilla/5.0 Python Terminal Renderer"
        }
    )

    with urlopen(
        req,
        timeout=20
    ) as response:
        data = response.read()

    return Image.open(
        BytesIO(data)
    ).convert("RGB")


def load_img(url, width):
    img = fetch_online_image(
        url
    )

    original_width, original_height = img.size

    aspect = (
        original_height
        / original_width
    )

    # Terminal characters are taller than wide.
    internal_width = max(
        20,
        int(width * 1.65)
    )

    internal_height = int(
        internal_width
        * aspect
        * 0.50
    )

    max_output_lines = get_render_height()

    max_internal_height = (
        max_output_lines * 2
    )

    if internal_height > max_internal_height:
        scale = (
            max_internal_height
            / internal_height
        )

        internal_width = int(
            internal_width * scale
        )

        internal_height = int(
            internal_height * scale
        )

    if internal_height < 2:
        internal_height = 2

    if internal_height % 2:
        internal_height += 1

    img = img.resize(
        (
            internal_width,
            internal_height
        ),
        Image.LANCZOS
    )

    img = ImageEnhance.Contrast(
        img
    ).enhance(1.7)

    img = ImageEnhance.Sharpness(
        img
    ).enhance(1.8)

    return img


def tint(r, g, b):
    luminance = int(
        r * 0.299
        + g * 0.587
        + b * 0.114
    )

    if luminance < 18:
        return (
            0,
            0,
            0
        )

    return (
        int(luminance * 0.35),
        min(
            255,
            int(luminance * 1.05)
        ),
        int(luminance * 0.48)
    )


def build_truecolor(img):
    pixels = img.load()

    lines = []

    for y in range(
        0,
        img.height - 1,
        2
    ):
        parts = []

        for x in range(
            img.width
        ):
            top = pixels[
                x,
                y
            ]

            bottom = pixels[
                x,
                y + 1
            ]

            tr1, tg1, tb1 = tint(
                *top
            )

            tr2, tg2, tb2 = tint(
                *bottom
            )

            if (
                tr1 + tg1 + tb1 < 10
                and
                tr2 + tg2 + tb2 < 10
            ):
                parts.append(" ")
                continue

            parts.append(
                fg(
                    tr1,
                    tg1,
                    tb1
                )
                + bg(
                    tr2,
                    tg2,
                    tb2
                )
                + CHAR_IMAGE
                + RESET
            )

        lines.append(
            "".join(parts)
        )

    return lines[
        :get_render_height()
    ]


def build_ascii(img):
    chars = " .:-=+*#%@"

    grayscale = img.convert(
        "L"
    )

    lines = []

    max_lines = get_render_height()

    width = min(
        img.width,
        get_safe_width(DEFAULT_WIDTH)
    )

    aspect = (
        grayscale.height
        / grayscale.width
    )

    height = max(
        2,
        int(
            width
            * aspect
            * 0.45
        )
    )

    height = min(
        height,
        max_lines
    )

    grayscale = grayscale.resize(
        (
            width,
            height
        ),
        Image.LANCZOS
    )

    pixels = grayscale.load()

    for y in range(height):
        row = []

        for x in range(width):
            value = pixels[
                x,
                y
            ]

            index = int(
                value
                / 255
                * (
                    len(chars) - 1
                )
            )

            row.append(
                chars[index]
            )

        lines.append(
            GREEN2
            + "".join(row)
            + RESET
        )

    return lines


def build(img):
    if TRUECOLOR_SUPPORTED and UTF8_OK:
        return build_truecolor(
            img
        )

    return build_ascii(
        img
    )


# ============================================================
# RENDER
# ============================================================

def corrupt_line(
    text,
    probability=0.10
):
    if not ANSI_SUPPORTED:
        return "".join(
            random.choice(
                GLITCH_CHARS
            )
            if (
                char != " "
                and random.random()
                < probability
            )
            else char
            for char in text
        )

    output = []

    i = 0

    while i < len(text):
        if text[i] == "\033":
            end = i + 1

            while (
                end < len(text)
                and text[end] != "m"
            ):
                end += 1

            end += 1

            output.append(
                text[i:end]
            )

            i = end
            continue

        char = text[i]

        if (
            char != " "
            and random.random()
            < probability
        ):
            output.append(
                random.choice(
                    GLITCH_CHARS
                )
            )
        else:
            output.append(
                char
            )

        i += 1

    return "".join(output)


def render_screen(
    lines,
    amount,
    width,
    percent,
    noisy_line=None
):
    cls()

    print(
        BLACK_BG,
        end=""
    )

    print()

    print(
        center(
            BOLD
            + GREEN
            + "GHOST // IMAGE RECONSTRUCTION"
            + RESET,
            width
        )
    )

    print(
        center(
            DIM
            + GRAY_GREEN
            + "FRAMEBUFFER :: ACTIVE"
            + RESET,
            width
        )
    )

    print()

    bar_size = responsive_bar_size(
        width
    )

    filled = int(
        percent
        / 100
        * bar_size
    )

    progress = (
        CHAR_SIDE_L
        + GREEN
        + CHAR_FULL * filled
        + RESET
        + DARK_GREEN
        + CHAR_EMPTY
        * (
            bar_size
            - filled
        )
        + RESET
        + CHAR_SIDE_R
    )

    print(
        center(
            f"{progress} "
            f"{GREEN3}{percent:3d}%{RESET}",
            width
        )
    )

    print()

    for index in range(
        amount
    ):
        print(
            center(
                lines[index],
                width
            )
        )

    if noisy_line:
        print(
            center(
                noisy_line,
                width
            )
        )


def reveal(lines, width):
    total = len(lines)

    if not total:
        return

    for i in range(
        total + 1
    ):
        pct = int(
            i
            / total
            * 100
        )

        if i < total:
            noisy = corrupt_line(
                lines[i],
                random.uniform(
                    0.06,
                    0.15
                )
            )

            render_screen(
                lines,
                i,
                width,
                pct,
                noisy
            )

            time.sleep(0.035)

        render_screen(
            lines,
            min(i, total),
            width,
            pct
        )

        time.sleep(0.045)


# ============================================================
# FINAL SCREEN
# ============================================================

def final_screen(
    lines,
    width,
    show_access=True
):
    cls()

    print(
        BLACK_BG,
        end=""
    )

    print()

    print(
        center(
            DARK_GREEN
            + CHAR_EMPTY
            * min(
                34,
                width
            )
            + RESET,
            width
        )
    )

    if show_access:
        text = (
            BOLD
            + GREEN3
            + "ACCESS GRANTED"
            + RESET
        )
    else:
        text = " "

    print(
        center(
            text,
            width
        )
    )

    print(
        center(
            DIM
            + GRAY_GREEN
            + "identity reconstruction complete"
            + RESET,
            width
        )
    )

    print(
        center(
            DARK_GREEN
            + CHAR_EMPTY
            * min(
                34,
                width
            )
            + RESET,
            width
        )
    )

    print()

    for line in lines:
        print(
            center(
                line,
                width
            )
        )

    print()

    print(
        center(
            GREEN2
            + "[ STATUS: VERIFIED ]"
            + RESET,
            width
        )
    )


def blinking_access(
    lines,
    width
):
    visible = True

    while True:
        # Recalcula caso o terminal seja redimensionado.
        current_width = get_safe_width(
            width
        )

        final_screen(
            lines,
            current_width,
            visible
        )

        visible = not visible

        time.sleep(0.55)


# ============================================================
# ARGS
# ============================================================

def parse_args():
    """
    Exemplos:

        python main.py
        python main.py 90
        python main.py audio.mp3
        python main.py 90 audio.mp3
    """

    width = DEFAULT_WIDTH
    audio = None

    for arg in sys.argv[1:]:
        if arg.isdigit():
            width = int(arg)
        else:
            audio = arg

    width = max(
        MIN_WIDTH,
        min(
            width,
            MAX_WIDTH
        )
    )

    return (
        width,
        audio
    )


# ============================================================
# MAIN
# ============================================================

def main():
    requested_width, audio = parse_args()

    width = get_safe_width(
        requested_width
    )

    play_audio(
        audio
    )

    intro(
        width
    )

    suspense(
        width
    )

    print()

    print(
        center(
            GREEN2
            + "[ NET ] downloading source image..."
            + RESET,
            width
        )
    )

    img = load_img(
        DEFAULT_IMAGE_URL,
        width
    )

    print(
        center(
            GREEN3
            + "[ OK  ] source image acquired"
            + RESET,
            width
        )
    )

    time.sleep(0.35)

    lines = build(
        img
    )

    # Recalcula porque o terminal pode
    # ter sido redimensionado.
    width = get_safe_width(
        requested_width
    )

    reveal(
        lines,
        width
    )

    blinking_access(
        lines,
        requested_width
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        stop_audio()

        print(
            RESET
            + SHOW_CURSOR
        )

        print(
            "\n[ session terminated ]"
        )

    except Exception as exc:
        stop_audio()

        print(
            RESET
            + SHOW_CURSOR
        )

        print(
            f"\n[ fatal error ] {exc}"
        )

    finally:
        print(
            RESET
            + SHOW_CURSOR,
            end=""
        )
