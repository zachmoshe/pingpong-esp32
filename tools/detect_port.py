#!/usr/bin/env python3
"""
Detect the ESP32 serial port robustly.

Strategy:
1) Score ports by USB VID/PID + product/manufacturer strings typical of ESP32
   boards and their USB-UART bridges (CP210x, CH340, FTDI, Prolific, Espressif).
2) (Optional) --probe: confirm by talking to the bootloader via esptool.
3) Print the best matching port to stdout. Use --list to see details.

Usage:
  python tools/detect_port.py              # print best guess
  python tools/detect_port.py --probe      # verify with esptool before printing
  python tools/detect_port.py --list       # show all candidate ports & scores
  PORT=$(python tools/detect_port.py --probe) make run
"""
import sys, shutil, subprocess, argparse
from serial.tools import list_ports

# Known vendors (VID) and bridges often used with ESP32 dev boards
KNOWN_VIDS = {
    0x303A: "Espressif",      # native USB on S2/S3/C3 or JTAG/serial
    0x10C4: "Silicon Labs",   # CP210x
    0x1A86: "QinHeng",        # CH340/CH341
    0x0403: "FTDI",           # FT232/FT231
    0x067B: "Prolific",       # PL2303
}

KEYWORDS = (
    "esp32", "espressif", "usb jtag", "cp210", "ch340", "ftdi", "pl2303",
    "usb-serial", "usb serial"
)

def port_score(p):
    """Heuristic score: VID match + keyword matches + mac 'cu.' preference."""
    score = 0
    if p.vid in KNOWN_VIDS:
        score += 4
    desc = " ".join(filter(None, [p.description, p.manufacturer, p.product])).lower()
    for kw in KEYWORDS:
        if kw in desc:
            score += 1
    # mac tip: prefer /dev/cu.* over /dev/tty.* for outgoing connections
    if p.device.startswith("/dev/cu."):
        score += 1
    # prefer usb* or USB* names
    if "usb" in p.device.lower():
        score += 1
    return score

def esptool_probe(port, timeout=8):
    """Run esptool to see if a real ESP responds on this port."""
    exe = shutil.which("esptool.py") or shutil.which("esptool")
    if not exe:
        return False, "esptool not found"
    cmd = [exe, "--chip", "auto", "--port", port, "--baud", "115200", "chip_id"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=timeout, check=False, text=True)
        ok = (proc.returncode == 0) and ("Detecting chip type" in proc.stdout or "Chip is" in proc.stdout)
        return ok, proc.stdout.strip()
    except Exception as e:
        return False, str(e)

def list_candidates():
    ports = list(list_ports.comports())
    # prefer cu.* duplicates on mac if both tty.* and cu.* exist for same base
    by_dev = {}
    for p in ports:
        base = p.device.replace("/dev/tty.", "/dev/").replace("/dev/cu.", "/dev/")
        if base not in by_dev:
            by_dev[base] = p
        else:
            # prefer cu.* over tty.*
            if p.device.startswith("/dev/cu."):
                by_dev[base] = p
    return list(by_dev.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="verify with esptool before printing")
    ap.add_argument("--list", action="store_true", help="list candidates with scores")
    args = ap.parse_args()

    candidates = list_candidates()
    if not candidates:
        print("/dev/ttyUSB0", end="")
        return

    scored = sorted(candidates, key=port_score, reverse=True)

    if args.list:
        for p in scored:
            print(f"{p.device:30} score={port_score(p):2d}  "
                  f"VID:PID={p.vid or 0:04X}:{p.pid or 0:04X}  "
                  f"{p.manufacturer or ''} {p.product or ''}  [{p.description}]")
        return

    best = None
    if args.probe:
        for p in scored:
            ok, _ = esptool_probe(p.device)
            if ok:
                best = p
                break
    if best is None:
        best = scored[0]

    print(best.device, end="")

if __name__ == "__main__":
    main()
