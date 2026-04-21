# -*- coding: utf-8 -*-
import sys
import os
import time
import random
import subprocess
from io import BytesIO
from urllib.request import urlopen, Request
from PIL import Image, ImageEnhance

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

GREEN = "\033[38;2;0;255;110m"
GREEN2 = "\033[38;2;0;210;80m"
GREEN3 = "\033[38;2;120;255;160m"
DARK = "\033[38;2;0;90;30m"
RED = "\033[38;2;255;80;80m"
BLACK_BG = "\033[40m"

DEFAULT_IMAGE_URL = "https://raw.githubusercontent.com/Ghosthszz/cmd/c8ee1a2fd69d37daeaa25144ad053431575da4fb/logo.jpg"
DEFAULT_WIDTH = 100

def fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
def bg(r,g,b): return f"\033[48;2;{r};{g};{b}m"

def cls():
    print("\033[2J\033[H", end="")

def center(text, width):
    if len(text) >= width:
        return text
    return " " * ((width - len(text)) // 2) + text

def get_terminal_size():
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except:
        return 100, 36

def get_safe_width(preferred=DEFAULT_WIDTH):
    term_w, _ = get_terminal_size()
    return max(40, min(preferred, term_w - 4))

def get_max_render_lines():
    _, term_h = get_terminal_size()
    return max(8, term_h - 10)

def glitch(text, p=0.04):
    pool = "/\\_|:.`~-=+"
    return "".join(random.choice(pool) if c != " " and random.random() < p else c for c in text)

def type_line(text, color, w):
    text = center(text, w)
    out = ""
    for c in text:
        out += c
        print(f"\r{BLACK_BG}{color}{out}{RESET}", end="", flush=True)
        time.sleep(0.012)
    print()

def bar(label, total, w, speed, color):
    print(center(color + label + RESET, w))
    for i in range(total + 1):
        pct = int(i / total * 100)
        print("\r" + center(color + "[" + "█" * i + " " * (total - i) + f"] {pct:3d}%" + RESET, w), end="")
        time.sleep(speed + random.uniform(0, 0.03))
    print("\n")

def stuck_bar(label, w):
    print(center(GREEN2 + label + RESET, w))
    total = 36
    for i in range(34):
        pct = int(i / total * 100)
        print("\r" + center(GREEN2 + "[" + "█" * i + " " * (total - i) + f"] {pct:3d}%" + RESET, w), end="")
        time.sleep(0.05)
    for _ in range(6):
        pct = random.choice([97, 98, 99])
        print("\r" + center(RED + "[" + "█" * 35 + " " + f"] {pct:3d}%" + RESET, w), end="")
        time.sleep(0.4)
    print("\r" + center(GREEN3 + "[" + "█" * 36 + "] 100%" + RESET, w))
    print()

def intro(w):
    cls()
    print(BLACK_BG, end="")
    lines = [
        "[root@blk ~]# starting protocol...",
        "[ok] framebuffer ready",
        "[ok] ghost session started",
        "[scan] bypassing trace..."
    ]
    for l in lines:
        type_line(glitch(l, 0.01), GREEN, w)
        time.sleep(0.2)

    print()
    bar("injecting payload", 30, w, 0.04, GREEN)
    bar("decrypting sectors", 28, w, 0.045, GREEN2)
    stuck_bar("forging mask", w)

def suspense(w):
    msgs = [
        "binding glyph layers...",
        "injecting noise...",
        "stabilizing render...",
        "forging edges...",
        "loading shadow map..."
    ]
    for _ in range(10):
        print(center(DIM + DARK + random.choice(msgs) + RESET, w))
        time.sleep(random.uniform(0.2, 0.4))

def play_audio(path):
    if not path:
        return
    try:
        subprocess.Popen(["termux-media-player", "play", path])
    except:
        pass

def stop_audio():
    try:
        subprocess.run(["termux-media-player", "stop"])
    except:
        pass

def fetch_online_image(url):
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    with urlopen(req, timeout=20) as response:
        data = response.read()
    return Image.open(BytesIO(data)).convert("RGB")

def load_img(url, w):
    img = fetch_online_image(url)

    aw, ah = img.size
    aspect = ah / aw

    new_w = int(w * 1.8)
    new_h = int(new_w * aspect * 0.55)

    max_render_lines = get_max_render_lines()
    max_internal_h = max_render_lines * 2

    if new_h > max_internal_h:
        scale = max_internal_h / new_h
        new_h = int(new_h * scale)
        new_w = int(new_w * scale)

    if new_h % 2:
        new_h += 1

    img = img.resize((new_w, new_h), Image.LANCZOS)

    img = ImageEnhance.Contrast(img).enhance(1.8)
    img = ImageEnhance.Sharpness(img).enhance(2.2)

    return img

def tint(r, g, b):
    lum = (r + g + b) // 3

    if lum < 18:
        return (0, 0, 0)

    return (
        int(lum * 0.65),
        int(min(255, lum * 1.0)),
        int(lum * 0.65)
    )

def build(img):
    px = img.load()
    lines = []

    for y in range(0, img.height - 1, 2):
        line = []
        for x in range(img.width):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, y + 1]
            tr1, tg1, tb1 = tint(r1, g1, b1)
            tr2, tg2, tb2 = tint(r2, g2, b2)
            if (tr1 + tg1 + tb1) < 10 and (tr2 + tg2 + tb2) < 10:
                line.append(" ")
            else:
                line.append(f"{fg(tr1,tg1,tb1)}{bg(tr2,tg2,tb2)}▀{RESET}")
        lines.append("".join(line))

    max_lines = get_max_render_lines()
    return lines[:max_lines]

def reveal(lines, w):
    total = len(lines)
    title = "[root@blk ~]# rendering attack..."

    for i in range(total + 1):
        flickers = random.randint(6, 12)

        for _ in range(flickers):
            cls()
            print(BLACK_BG, end="")
            print(center(GREEN + title + RESET, w))

            pct = int(i / total * 100) if total else 100
            fake = pct + random.randint(-2, 2)
            print(center(GREEN2 + f"[ render ] {fake:3d}%" + RESET, w))
            print()

            for j in range(i):
                print(center(lines[j], w))

            if i < total:
                noisy = []
                src = lines[i]
                k = 0
                while k < len(src):
                    if src[k] == "\033":
                        e = k + 1
                        while e < len(src) and src[e] != "m":
                            e += 1
                        e += 1
                        noisy.append(src[k:e])
                        k = e
                        continue

                    ch = src[k]
                    if ch != " " and random.random() < 0.2:
                        noisy.append(random.choice("█▓▒░/\\_|"))
                    else:
                        noisy.append(ch)
                    k += 1

                print(center("".join(noisy), w))
                print()
                print(center(DIM + DARK + "stabilizing..." + RESET, w))

            time.sleep(random.uniform(0.10, 0.20))

        cls()
        print(BLACK_BG, end="")
        print(center(GREEN + title + RESET, w))
        print(center(GREEN2 + f"[ render ] {pct:3d}%" + RESET, w))
        print()

        for j in range(i):
            print(center(lines[j], w))

        if i < total:
            print(center(lines[i], w))

        time.sleep(random.uniform(0.15, 0.25))

def blinking_access(w):
    text = center(BOLD + GREEN + "[ ACCESS GRANTED ]" + RESET, w)
    blank = center(" ", w)

    while True:
        print(text)
        time.sleep(0.5)

        print("\033[F", end="")
        print(blank)

        print("\033[F", end="")
        time.sleep(0.5)

def parse_args():
    """
    Formas aceitas:
    python main.py
    python main.py 90
    python main.py som.mp3
    python main.py 90 som.mp3
    """
    width = DEFAULT_WIDTH
    audio = None

    args = sys.argv[1:]

    for arg in args:
        if arg.isdigit():
            width = int(arg)
        else:
            audio = arg

    return width, audio

def main():
    width, audio = parse_args()

    w = get_safe_width(width)

    play_audio(audio)

    intro(w)
    suspense(w)

    img = load_img(DEFAULT_IMAGE_URL, w)
    lines = build(img)

    w = get_safe_width(width)
    reveal(lines, w)

    print()
    blinking_access(w)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop_audio()
        print(RESET)
