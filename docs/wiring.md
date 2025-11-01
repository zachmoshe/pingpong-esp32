# Wiring notes

- **LED**: use onboard LED on GPIO2 (already set in `device/main.py`).
- **Button**: connect a momentary pushbutton between GPIO0 and GND (uses internal pull-up).
- Add more sensors in `device/drivers/` and spawn a coroutine in `main.py`.
