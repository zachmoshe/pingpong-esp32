# pingpong-esp32 (MicroPython on ESP32)

A clean starter for developing an ESP32 project with **MicroPython** on macOS.

## Quick start

```bash
# 1) Prepare Python env with uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv && source .venv/bin/activate
uv sync --extra dev

# 2) Download the correct MicroPython firmware for your chip into ./firmware/
#    e.g., esp32-<version>.bin (ESP32 / ESP32-S3 / ESP32-C3 differ!)

# 3) Flash (first time only)
make flash BIN=firmware/<your-firmware>.bin

# 4) Copy and edit Wi‑Fi secrets (no reflashing needed)
cp device/secrets.example.json device/secrets.json
$EDITOR device/secrets.json

# 5) Sync code and run
make run   # (sync + reset)
make repl  # open a REPL
```

## Layout

```
pingpong-esp32/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ pyproject.toml
├─ Makefile
├─ tools/
│  └─ detect_port.py
├─ firmware/
│  └─ (put .bin here)
├─ device/
│  ├─ boot.py
│  ├─ main.py
│  ├─ lib/              (vendored MicroPython libs)
│  ├─ drivers/
│  │  ├─ button.py
│  │  └─ led.py
│  ├─ net/
│  │  ├─ wifi_manager.py
│  │  └─ ntp.py
│  └─ secrets.example.json
├─ host/
│  └─ cli.py            (placeholder for future Slack/diagnostics)
└─ docs/
   └─ wiring.md
```

## Notes
- `device/secrets.json` is **.gitignored** and can be pushed over serial any time.
- If multiple serial ports are present, set `PORT=/dev/tty.usbserial-...` explicitly.
- Use `Ctrl-D` to soft‑reboot from REPL; `Ctrl-]` to exit `mpremote`.

## Backend: Docker deploy (Linux VM)
- Copy `env.example` to `.env` and fill `SLACK_BOT_TOKEN` (and `NGROK_AUTH_TOKEN` if you keep ngrok on in `backend/config.json`).
- Build and start: `docker compose up -d --build`.
- Update to a new version: pull/code sync, then `docker compose up -d --build` again.
- Host port is configurable via `BACKEND_PORT` in `.env` (container always listens on 12345).
- To view logs: `docker compose logs -f backend`.
